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
        """Lê as linhas de itens do formulário de entrega."""
        nomes = request.form.getlist("item_nome[]")
        epi_ids = request.form.getlist("item_epi_id[]")
        cas = request.form.getlist("item_ca[]")
        qtdes = request.form.getlist("item_qtde[]")
        tams = request.form.getlist("item_tamanho[]")
        salvar = request.form.getlist("item_salvar[]")
        itens = []
        for i, nome in enumerate(nomes):
            nome = (nome or "").strip()
            if not nome:
                continue
            try:
                quantidade = float((qtdes[i] if i < len(qtdes) else "1").replace(",", ".") or 1)
            except ValueError:
                quantidade = 1.0
            epi_id = (epi_ids[i] if i < len(epi_ids) else "") or ""
            itens.append({
                "epi_id": int(epi_id) if epi_id.isdigit() else None,
                "nome": nome.upper(),
                "ca": (cas[i] if i < len(cas) else "").strip(),
                "quantidade": quantidade,
                "tamanho": (tams[i] if i < len(tams) else "").strip().upper(),
                "salvar": (salvar[i] if i < len(salvar) else "0") == "1",
            })
        return itens

    def gravar_itens(entrega_id, itens):
        con = db()
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
                        (item["nome"], item["ca"], 1 if item["tamanho"] else 0),
                    ).lastrowid
            con.execute(
                "INSERT INTO entrega_itens (entrega_id, epi_id, nome, ca, quantidade, tamanho, ordem)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (entrega_id, epi_id, item["nome"], item["ca"], item["quantidade"], item["tamanho"], ordem),
            )

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
                "SELECT * FROM entrega_itens WHERE entrega_id = ? ORDER BY ordem, id", (e["id"],)
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
                if assinatura_id:
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
            data_devolucao = (request.form.get("data_devolucao") or "").strip() or None
            observacoes = (request.form.get("observacoes") or "").strip()
            lista = itens_do_formulario()
            if not lista:
                flash("Inclua ao menos um item na entrega.", "erro")
                return render_template("entrega_form.html", funcionario=f, epis=epis,
                                       entrega=entrega, itens=itens)
            assinatura_id = database.salvar_assinatura(request.form.get("assinatura"))
            assinatura_dev_id = database.salvar_assinatura(request.form.get("assinatura_devolucao"))

            if entrega is None:
                eid = con.execute(
                    "INSERT INTO entregas (funcionario_id, data_inicio, data_entrega, assinatura_id,"
                    " data_devolucao, assinatura_devolucao_id, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (fid, data_inicio, data_entrega, assinatura_id, data_devolucao,
                     assinatura_dev_id, observacoes),
                ).lastrowid
                msg = "Entrega registrada."
            else:
                if assinatura_id:
                    database.apagar_assinatura(entrega["assinatura_id"])
                    con.execute("UPDATE entregas SET assinatura_id = ? WHERE id = ?", (assinatura_id, eid))
                if assinatura_dev_id:
                    database.apagar_assinatura(entrega["assinatura_devolucao_id"])
                    con.execute("UPDATE entregas SET assinatura_devolucao_id = ? WHERE id = ?",
                                (assinatura_dev_id, eid))
                con.execute(
                    "UPDATE entregas SET data_inicio = ?, data_entrega = ?, data_devolucao = ?,"
                    " observacoes = ? WHERE id = ?",
                    (data_inicio, data_entrega, data_devolucao, observacoes, eid),
                )
                msg = "Entrega atualizada."
            gravar_itens(eid, lista)
            con.commit()
            flash(msg, "ok")
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
            assinatura_id = database.salvar_assinatura(request.form.get("assinatura_devolucao"))
            if assinatura_id:
                database.apagar_assinatura(entrega["assinatura_devolucao_id"])
                con.execute("UPDATE entregas SET assinatura_devolucao_id = ? WHERE id = ?", (assinatura_id, eid))
            con.execute("UPDATE entregas SET data_devolucao = ? WHERE id = ?", (data_devolucao, eid))
            con.commit()
            flash("Devolução registrada.", "ok")
            return redirect(url_for("ficha", fid=f["id"]))
        return render_template("devolucao.html", funcionario=f, entrega=entrega, itens=itens)

    @app.post("/entregas/<int:eid>/excluir")
    def entrega_excluir(eid):
        con = db()
        entrega = con.execute("SELECT * FROM entregas WHERE id = ?", (eid,)).fetchone()
        if entrega is None:
            abort(404)
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
            (nome, (request.form.get("ca") or "").strip(), 1 if request.form.get("tem_tamanho") else 0),
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
             1 if request.form.get("tem_tamanho") else 0,
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
            itens = con.execute(
                "SELECT * FROM entrega_itens WHERE entrega_id = ? ORDER BY ordem, id", (e["id"],)
            ).fetchall()
            blocos.append({
                "entrega": e,
                "itens": [dict(i) for i in itens],
                "assinatura": _blob_assinatura(con, e["assinatura_id"]),
                "assinatura_devolucao": _blob_assinatura(con, e["assinatura_devolucao_id"]),
            })
        conteudo = pdf_ficha.gerar_ficha(
            database.empresa(), f, blocos, _blob_assinatura(con, f["assinatura_admissao_id"])
        )
        nome = "".join(c for c in f["nome"] if c.isalnum() or c in " -_").strip().replace(" ", "_")
        return send_file(
            _bytes_io(conteudo), mimetype="application/pdf",
            as_attachment=False, download_name=f"ficha_epi_{nome or f['id']}.pdf",
        )

    return app


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
