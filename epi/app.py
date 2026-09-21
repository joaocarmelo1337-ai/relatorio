"""Controle de Entrega de EPI — aplicativo Flask com banco SQLite."""
import os
from datetime import date

from flask import (
    Flask, Response, abort, flash, g, redirect, render_template, request,
    send_file, url_for,
)

import db as database
import pdf as pdf_ficha

TAMANHOS = ["P", "M", "G", "GG", "EXG"]
TIPOS_TAMANHO = database.ROTULO_TAMANHO
IMAGENS_OK = {"image/png", "image/jpeg", "image/jpg", "image/gif", "image/webp", "image/svg+xml"}


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "epi-dev-key-troque-em-producao"),
        DATABASE=os.environ.get("EPI_DATABASE", os.path.join(app.instance_path, "epi.sqlite3")),
        MAX_CONTENT_LENGTH=12 * 1024 * 1024,   # uploads/assinaturas
    )
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)
    database.init_app(app)

    # ------------------------------------------------------------ utilidades

    @app.context_processor
    def injetar_globais():
        emp = database.empresa()
        return {
            "empresa": emp,
            "tem_logo": bool(emp and emp["logo"]),
            "hoje": date.today().isoformat(),
            "TAMANHOS": TAMANHOS,
            "TIPOS_TAMANHO": TIPOS_TAMANHO,
        }

    @app.template_filter("data_br")
    def data_br(iso):
        return pdf_ficha._br(iso)

    @app.template_filter("qtd")
    def qtd(v):
        return pdf_ficha._num(v)

    def db():
        return database.get_db()

    def buscar_funcionario(fid):
        f = db().execute("SELECT * FROM funcionarios WHERE id = ?", (fid,)).fetchone()
        if f is None:
            abort(404)
        return f

    def itens_do_formulario():
        """Lê as linhas de itens do formulário de entrega.

        Cada material carrega a sua própria assinatura: ou uma nova, colhida
        agora (PNG em base64), ou a que já estava gravada (id da assinatura).
        """
        nomes = request.form.getlist("item_nome[]")
        epi_ids = request.form.getlist("item_epi_id[]")
        cas = request.form.getlist("item_ca[]")
        qtdes = request.form.getlist("item_qtde[]")
        tams = request.form.getlist("item_tamanho[]")
        salvar = request.form.getlist("item_salvar[]")
        assinaturas = request.form.getlist("item_assinatura[]")
        assinaturas_id = request.form.getlist("item_assinatura_id[]")
        apagar = request.form.getlist("item_assinatura_apagar[]")
        devolucoes = request.form.getlist("item_data_devolucao[]")
        devolucoes_id = request.form.getlist("item_assinatura_devolucao_id[]")

        def pega(lista, i):
            return lista[i] if i < len(lista) else ""

        itens = []
        for i, nome in enumerate(nomes):
            nome = (nome or "").strip()
            if not nome:
                continue
            try:
                quantidade = float((pega(qtdes, i) or "1").replace(",", ".") or 1)
            except ValueError:
                quantidade = 1.0
            epi_id = pega(epi_ids, i) or ""
            antiga = pega(assinaturas_id, i)
            itens.append({
                "epi_id": int(epi_id) if epi_id.isdigit() else None,
                "nome": nome.upper(),
                "ca": pega(cas, i).strip(),
                "quantidade": quantidade,
                "tamanho": pega(tams, i).strip().upper(),
                "salvar": pega(salvar, i) == "1",
                "assinatura_nova": pega(assinaturas, i),
                "assinatura_id": int(antiga) if antiga.isdigit() else None,
                "apagar_assinatura": pega(apagar, i) == "1",
                "data_devolucao": pega(devolucoes, i).strip() or None,
                "assinatura_devolucao_id": (
                    int(pega(devolucoes_id, i)) if pega(devolucoes_id, i).isdigit() else None
                ),
            })
        return itens

    def gravar_itens(entrega_id, itens):
        con = db()
        # assinaturas que sobrarem (item removido ou substituído) são apagadas
        antigas = {
            r["id"]: (r["assinatura_id"], r["assinatura_devolucao_id"])
            for r in con.execute(
                "SELECT id, assinatura_id, assinatura_devolucao_id FROM entrega_itens WHERE entrega_id = ?",
                (entrega_id,),
            )
        }
        usadas = set()
        con.execute("DELETE FROM entrega_itens WHERE entrega_id = ?", (entrega_id,))

        for ordem, item in enumerate(itens):
            epi_id = item["epi_id"]
            if item["salvar"] and epi_id is None:
                existente = con.execute(
                    "SELECT id FROM epi_master WHERE nome = ?", (item["nome"],)
                ).fetchone()
                if existente:
                    epi_id = existente["id"]
                else:
                    epi_id = con.execute(
                        "INSERT INTO epi_master (nome, ca, tem_tamanho) VALUES (?, ?, ?)",
                        (item["nome"], item["ca"], _tipo_pelo_tamanho(item["tamanho"])),
                    ).lastrowid

            assinatura_id = database.salvar_assinatura(item["assinatura_nova"])
            if assinatura_id is None and not item["apagar_assinatura"]:
                assinatura_id = item["assinatura_id"]          # mantém a que já existia
            if assinatura_id:
                usadas.add(assinatura_id)
            if item["assinatura_devolucao_id"]:
                usadas.add(item["assinatura_devolucao_id"])

            con.execute(
                "INSERT INTO entrega_itens (entrega_id, epi_id, nome, ca, quantidade, tamanho,"
                " assinatura_id, data_devolucao, assinatura_devolucao_id, ordem)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (entrega_id, epi_id, item["nome"], item["ca"], item["quantidade"], item["tamanho"],
                 assinatura_id, item["data_devolucao"], item["assinatura_devolucao_id"], ordem),
            )

        for recebimento, devolucao in antigas.values():
            for aid in (recebimento, devolucao):
                if aid and aid not in usadas:
                    database.apagar_assinatura(aid)

    def historico(funcionario_id):
        con = db()
        entregas = con.execute(
            "SELECT * FROM entregas WHERE funcionario_id = ?"
            " ORDER BY date(data_entrega) DESC, id DESC",
            (funcionario_id,),
        ).fetchall()
        blocos = []
        for e in entregas:
            itens = con.execute(
                "SELECT i.*, COALESCE(p.tem_tamanho, 0) AS tem_tamanho"
                " FROM entrega_itens i LEFT JOIN epi_master p ON p.id = i.epi_id"
                " WHERE i.entrega_id = ? ORDER BY i.ordem, i.id", (e["id"],)
            ).fetchall()
            blocos.append({"entrega": e, "itens": itens})
        return blocos

    # ------------------------------------------------------------ funcionários

    @app.route("/")
    def index():
        return redirect(url_for("funcionarios"))

    @app.route("/funcionarios")
    def funcionarios():
        busca = (request.args.get("q") or "").strip()
        sql = (
            "SELECT f.*,"
            " (SELECT COUNT(*) FROM entregas e WHERE e.funcionario_id = f.id) AS total_entregas,"
            " (SELECT MAX(date(e.data_entrega)) FROM entregas e WHERE e.funcionario_id = f.id) AS ultima_entrega"
            " FROM funcionarios f"
        )
        params = []
        if busca:
            sql += " WHERE f.nome LIKE ? OR f.registro LIKE ? OR f.cargo LIKE ? OR f.setor LIKE ?"
            params = [f"%{busca}%"] * 4
        sql += " ORDER BY f.nome COLLATE PT"
        lista = db().execute(sql, params).fetchall()
        return render_template("funcionarios.html", funcionarios=lista, busca=busca)

    @app.route("/funcionarios/novo", methods=["GET", "POST"])
    @app.route("/funcionarios/<int:fid>/editar", methods=["GET", "POST"])
    def funcionario_form(fid=None):
        f = buscar_funcionario(fid) if fid else None
        if request.method == "POST":
            nome = (request.form.get("nome") or "").strip()
            if not nome:
                flash("O nome do funcionário é obrigatório.", "erro")
                return render_template("funcionario_form.html", funcionario=f or request.form)
            dados = (
                nome,
                (request.form.get("registro") or "").strip(),
                (request.form.get("cargo") or "").strip(),
                (request.form.get("setor") or "").strip(),
                (request.form.get("ciente_data") or "").strip() or None,
            )
            assinatura_id = database.salvar_assinatura(request.form.get("assinatura"))
            apagar_assinatura = request.form.get("assinatura_apagar") == "1"
            con = db()
            if f is None:
                cur = con.execute(
                    "INSERT INTO funcionarios (nome, registro, cargo, setor, ciente_data, assinatura_admissao_id)"
                    " VALUES (?, ?, ?, ?, ?, ?)",
                    dados + (assinatura_id,),
                )
                fid = cur.lastrowid
                msg = "Funcionário cadastrado."
            else:
                if assinatura_id or apagar_assinatura:
                    database.apagar_assinatura(f["assinatura_admissao_id"])
                    con.execute(
                        "UPDATE funcionarios SET assinatura_admissao_id = ? WHERE id = ?", (assinatura_id, fid)
                    )
                con.execute(
                    "UPDATE funcionarios SET nome = ?, registro = ?, cargo = ?, setor = ?, ciente_data = ?"
                    " WHERE id = ?",
                    dados + (fid,),
                )
                msg = "Funcionário atualizado."
            con.commit()
            flash(msg, "ok")
            return redirect(url_for("ficha", fid=fid))
        return render_template("funcionario_form.html", funcionario=f)

    @app.post("/funcionarios/<int:fid>/excluir")
    def funcionario_excluir(fid):
        f = buscar_funcionario(fid)
        con = db()
        con.execute("DELETE FROM funcionarios WHERE id = ?", (fid,))
        database.apagar_assinatura(f["assinatura_admissao_id"])
        con.commit()
        flash(f"Funcionário {f['nome']} excluído.", "ok")
        return redirect(url_for("funcionarios"))

    @app.route("/funcionarios/<int:fid>")
    def ficha(fid):
        f = buscar_funcionario(fid)
        return render_template("ficha.html", funcionario=f, historico=historico(fid))

    # ------------------------------------------------------------ entregas

    @app.route("/funcionarios/<int:fid>/entregas/nova", methods=["GET", "POST"])
    @app.route("/entregas/<int:eid>/editar", methods=["GET", "POST"])
    def entrega_form(fid=None, eid=None):
        con = db()
        entrega = itens = None
        if eid:
            entrega = con.execute("SELECT * FROM entregas WHERE id = ?", (eid,)).fetchone()
            if entrega is None:
                abort(404)
            fid = entrega["funcionario_id"]
            itens = con.execute(
                "SELECT * FROM entrega_itens WHERE entrega_id = ? ORDER BY ordem, id", (eid,)
            ).fetchall()
        f = buscar_funcionario(fid)
        epis = con.execute("SELECT * FROM epi_master WHERE ativo = 1 ORDER BY nome COLLATE PT").fetchall()

        if request.method == "POST":
            data_entrega = (request.form.get("data_entrega") or "").strip() or date.today().isoformat()
            data_inicio = (request.form.get("data_inicio") or "").strip() or None
            observacoes = (request.form.get("observacoes") or "").strip()
            lista = itens_do_formulario()
            if not lista:
                flash("Inclua ao menos um item na entrega.", "erro")
                return render_template("entrega_form.html", funcionario=f, epis=epis,
                                       entrega=entrega, itens=itens)

            if entrega is None:
                eid = con.execute(
                    "INSERT INTO entregas (funcionario_id, data_inicio, data_entrega, observacoes)"
                    " VALUES (?, ?, ?, ?)",
                    (fid, data_inicio, data_entrega, observacoes),
                ).lastrowid
                msg = "Entrega registrada."
            else:
                con.execute(
                    "UPDATE entregas SET data_inicio = ?, data_entrega = ?, observacoes = ? WHERE id = ?",
                    (data_inicio, data_entrega, observacoes, eid),
                )
                msg = "Entrega atualizada."
            gravar_itens(eid, lista)
            con.commit()

            sem_assinatura = [
                i["nome"] for i in con.execute(
                    "SELECT nome FROM entrega_itens WHERE entrega_id = ? AND assinatura_id IS NULL"
                    " ORDER BY ordem, id", (eid,)
                )
            ]
            if sem_assinatura:
                flash("Sem assinatura ainda: " + ", ".join(sem_assinatura) +
                      ". Cada material precisa da assinatura de quem recebeu — abra em Editar para colher.",
                      "erro")
            else:
                flash(msg + " Todos os materiais estão assinados.", "ok")
            return redirect(url_for("ficha", fid=fid))

        return render_template("entrega_form.html", funcionario=f, epis=epis, entrega=entrega, itens=itens)

    @app.route("/entregas/<int:eid>/devolucao", methods=["GET", "POST"])
    def devolucao(eid):
        con = db()
        entrega = con.execute("SELECT * FROM entregas WHERE id = ?", (eid,)).fetchone()
        if entrega is None:
            abort(404)
        f = buscar_funcionario(entrega["funcionario_id"])
        itens = con.execute(
            "SELECT * FROM entrega_itens WHERE entrega_id = ? ORDER BY ordem, id", (eid,)
        ).fetchall()

        if request.method == "POST":
            data_devolucao = (request.form.get("data_devolucao") or "").strip() or None
            devolvidos = set(request.form.getlist("devolver[]"))
            if devolvidos and not data_devolucao:
                flash("Informe a data da devolução.", "erro")
                return render_template("devolucao.html", funcionario=f, entrega=entrega, itens=itens)

            sem_assinatura, total = [], 0
            for item in itens:
                iid = str(item["id"])
                if iid in devolvidos:
                    nova = database.salvar_assinatura(request.form.get(f"assinatura_{iid}"))
                    assinatura_id = nova or item["assinatura_devolucao_id"]
                    if nova and item["assinatura_devolucao_id"]:
                        database.apagar_assinatura(item["assinatura_devolucao_id"])
                    con.execute(
                        "UPDATE entrega_itens SET data_devolucao = ?, assinatura_devolucao_id = ? WHERE id = ?",
                        (data_devolucao, assinatura_id, item["id"]),
                    )
                    total += 1
                    if not assinatura_id:
                        sem_assinatura.append(item["nome"])
                elif item["data_devolucao"]:
                    database.apagar_assinatura(item["assinatura_devolucao_id"])
                    con.execute(
                        "UPDATE entrega_itens SET data_devolucao = NULL, assinatura_devolucao_id = NULL"
                        " WHERE id = ?", (item["id"],),
                    )
            con.commit()
            if sem_assinatura:
                flash("Devolução registrada, mas sem assinatura em: " + ", ".join(sem_assinatura) + ".", "erro")
            else:
                flash(f"Devolução registrada em {total} material(is)." if total
                      else "Devoluções atualizadas.", "ok")
            return redirect(url_for("ficha", fid=f["id"]))

        return render_template("devolucao.html", funcionario=f, entrega=entrega, itens=itens)

    @app.post("/entregas/<int:eid>/excluir")
    def entrega_excluir(eid):
        con = db()
        entrega = con.execute("SELECT * FROM entregas WHERE id = ?", (eid,)).fetchone()
        if entrega is None:
            abort(404)
        for item in con.execute(
            "SELECT assinatura_id, assinatura_devolucao_id FROM entrega_itens WHERE entrega_id = ?", (eid,)
        ).fetchall():
            database.apagar_assinatura(item["assinatura_id"])
            database.apagar_assinatura(item["assinatura_devolucao_id"])
        con.execute("DELETE FROM entregas WHERE id = ?", (eid,))
        database.apagar_assinatura(entrega["assinatura_id"])
        database.apagar_assinatura(entrega["assinatura_devolucao_id"])
        con.commit()
        flash("Entrega excluída.", "ok")
        return redirect(url_for("ficha", fid=entrega["funcionario_id"]))

    # ------------------------------------------------------------ lista mestre

    @app.route("/epis")
    def epis():
        lista = db().execute("SELECT * FROM epi_master ORDER BY ativo DESC, nome COLLATE PT").fetchall()
        return render_template("epis.html", epis=lista)

    @app.post("/epis/novo")
    def epi_novo():
        nome = (request.form.get("nome") or "").strip().upper()
        if not nome:
            flash("Informe o nome do EPI.", "erro")
            return redirect(url_for("epis"))
        con = db()
        if con.execute("SELECT 1 FROM epi_master WHERE nome = ?", (nome,)).fetchone():
            flash(f"{nome} já está na lista.", "erro")
            return redirect(url_for("epis"))
        con.execute(
            "INSERT INTO epi_master (nome, ca, tem_tamanho) VALUES (?, ?, ?)",
            (nome, (request.form.get("ca") or "").strip(), _tipo_tamanho(request.form.get("tem_tamanho"))),
        )
        con.commit()
        flash(f"{nome} adicionado à lista mestre.", "ok")
        return redirect(url_for("epis"))

    @app.post("/epis/<int:pid>/editar")
    def epi_editar(pid):
        nome = (request.form.get("nome") or "").strip().upper()
        if not nome:
            flash("Informe o nome do EPI.", "erro")
            return redirect(url_for("epis"))
        con = db()
        con.execute(
            "UPDATE epi_master SET nome = ?, ca = ?, tem_tamanho = ?, ativo = ? WHERE id = ?",
            (nome, (request.form.get("ca") or "").strip(),
             _tipo_tamanho(request.form.get("tem_tamanho")),
             1 if request.form.get("ativo") else 0, pid),
        )
        con.commit()
        flash("Item atualizado.", "ok")
        return redirect(url_for("epis"))

    @app.post("/epis/<int:pid>/excluir")
    def epi_excluir(pid):
        con = db()
        con.execute("DELETE FROM epi_master WHERE id = ?", (pid,))
        con.commit()
        flash("Item removido da lista mestre. As entregas já registradas foram preservadas.", "ok")
        return redirect(url_for("epis"))

    # ------------------------------------------------------------ configurações

    @app.route("/configuracoes", methods=["GET", "POST"])
    def configuracoes():
        con = db()
        if request.method == "POST":
            nome = (request.form.get("nome") or "").strip()
            cnpj = (request.form.get("cnpj") or "").strip()
            con.execute(
                "UPDATE empresa SET nome = ?, cnpj = ?, atualizado_em = datetime('now','localtime') WHERE id = 1",
                (nome, cnpj),
            )
            if request.form.get("remover_logo"):
                con.execute("UPDATE empresa SET logo = NULL, logo_mime = NULL WHERE id = 1")
            arquivo = request.files.get("logo")
            if arquivo and arquivo.filename:
                if arquivo.mimetype not in IMAGENS_OK:
                    flash("A logo deve ser uma imagem (PNG, JPG, GIF ou WEBP).", "erro")
                    return redirect(url_for("configuracoes"))
                con.execute(
                    "UPDATE empresa SET logo = ?, logo_mime = ? WHERE id = 1",
                    (arquivo.read(), arquivo.mimetype),
                )
            con.commit()
            flash("Configurações salvas.", "ok")
            return redirect(url_for("configuracoes"))
        return render_template("configuracoes.html")

    # ------------------------------------------------------------ imagens e PDF

    @app.route("/empresa/logo")
    def logo():
        emp = database.empresa()
        if not emp or not emp["logo"]:
            abort(404)
        return Response(bytes(emp["logo"]), mimetype=emp["logo_mime"] or "image/png",
                        headers={"Cache-Control": "no-cache"})

    @app.route("/assinaturas/<int:aid>.png")
    def assinatura(aid):
        row = db().execute("SELECT imagem, mime FROM assinaturas WHERE id = ?", (aid,)).fetchone()
        if row is None:
            abort(404)
        return Response(bytes(row["imagem"]), mimetype=row["mime"] or "image/png")

    @app.route("/funcionarios/<int:fid>/pdf")
    def ficha_pdf(fid):
        f = buscar_funcionario(fid)
        con = db()
        blocos = []
        entregas = con.execute(
            "SELECT * FROM entregas WHERE funcionario_id = ? ORDER BY date(data_entrega), id", (fid,)
        ).fetchall()
        for e in entregas:
            # tem_tamanho vem da lista mestre: é o que faz o PDF imprimir P/M/G/GG/EXG
            itens = con.execute(
                "SELECT i.*, COALESCE(p.tem_tamanho, 0) AS tem_tamanho"
                " FROM entrega_itens i LEFT JOIN epi_master p ON p.id = i.epi_id"
                " WHERE i.entrega_id = ? ORDER BY i.ordem, i.id", (e["id"],)
            ).fetchall()
            linhas = []
            for item in itens:
                dados = dict(item)
                # cada material leva a sua própria assinatura para a ficha
                dados["assinatura"] = _blob_assinatura(con, item["assinatura_id"])
                dados["assinatura_devolucao"] = _blob_assinatura(con, item["assinatura_devolucao_id"])
                linhas.append(dados)
            blocos.append({"entrega": e, "itens": linhas})
        conteudo = pdf_ficha.gerar_ficha(
            database.empresa(), f, blocos, _blob_assinatura(con, f["assinatura_admissao_id"])
        )
        nome = "".join(c for c in f["nome"] if c.isalnum() or c in " -_").strip().replace(" ", "_")
        return send_file(
            _bytes_io(conteudo), mimetype="application/pdf",
            as_attachment=False, download_name=f"ficha_epi_{nome or f['id']}.pdf",
        )

    return app


def _tipo_tamanho(valor):
    """Converte o que veio do formulário em 0 (nenhum), 1 (letra) ou 2 (numeração)."""
    try:
        v = int(valor)
    except (TypeError, ValueError):
        return database.SEM_TAMANHO
    return v if v in (database.TAM_LETRA, database.TAM_NUMERO) else database.SEM_TAMANHO


def _tipo_pelo_tamanho(tamanho):
    """Item criado na hora da entrega: deduz o tipo pelo tamanho digitado."""
    tamanho = (tamanho or "").strip().upper()
    if not tamanho:
        return database.SEM_TAMANHO
    return database.TAM_LETRA if tamanho in TAMANHOS else database.TAM_NUMERO


def _blob_assinatura(con, aid):
    if not aid:
        return None
    row = con.execute("SELECT imagem FROM assinaturas WHERE id = ?", (aid,)).fetchone()
    return bytes(row["imagem"]) if row else None


def _bytes_io(conteudo):
    import io
    return io.BytesIO(conteudo)


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
