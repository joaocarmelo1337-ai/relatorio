const fs=require('fs');
const d=require('docx');
const {Document,Packer,Paragraph,TextRun,HeadingLevel,AlignmentType,Table,TableRow,TableCell,WidthType,ShadingType,BorderStyle,ImageRun,PageBreak,TableOfContents,Header,Footer,PageNumber}=d;

const W=9000; // table total dxa
const ACC="C0392B";

function P(text,opt={}){return new Paragraph({spacing:{after:opt.after??120,before:opt.before??0},alignment:opt.align,children:[new TextRun({text,bold:opt.bold,italics:opt.italics,size:opt.size??22,color:opt.color,font:"Calibri"})]});}
function H(text,lvl){return new Paragraph({heading:lvl,spacing:{before:280,after:140},children:[new TextRun({text,font:"Calibri",bold:true,color:lvl===HeadingLevel.HEADING_1?ACC:"333333",size:lvl===HeadingLevel.HEADING_1?32:26})]});}
function bullet(text){return new Paragraph({bullet:{level:0},spacing:{after:80},children:[new TextRun({text,size:22,font:"Calibri"})]});}
function fml(text){return new Paragraph({spacing:{before:120,after:120},alignment:AlignmentType.CENTER,children:[new TextRun({text,size:24,font:"Cambria",italics:true,color:"1F3864"})]});}

function cell(t,{b=false,head=false,w}={}){
  return new TableCell({width:{size:w,type:WidthType.DXA},margins:{top:60,bottom:60,left:90,right:90},
    shading:head?{type:ShadingType.CLEAR,fill:"F2E4E1"}:undefined,
    children:[new Paragraph({spacing:{after:0},children:[new TextRun({text:t,bold:b||head,size:19,font:"Calibri"})]})]});
}
function table(rows,widths){
  return new Table({columnWidths:widths,width:{size:W,type:WidthType.DXA},
    rows:rows.map((r,i)=>new TableRow({tableHeader:i===0,children:r.map((c,j)=>cell(String(c),{head:i===0,w:widths[j]}))}))});
}
function img(file,wpx,cap){
  const buf=fs.readFileSync(file);
  const out=[new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:160,after:60},
    children:[new ImageRun({type:"png",data:buf,transformation:{width:wpx,height:Math.round(wpx*imgH(file)/imgW(file))}})]})];
  if(cap) out.push(new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:200},children:[new TextRun({text:cap,size:18,italics:true,color:"666666",font:"Calibri"})]}));
  return out;
}
const sizes=JSON.parse(fs.readFileSync('work/sizes.json','utf8'));
function imgW(f){return sizes[f][0];}
function imgH(f){return sizes[f][1];}

const K=[];
function add(...x){x.forEach(e=>K.push(e));}

// ---------- CAPA ----------
add(new Paragraph({spacing:{before:2600,after:0},alignment:AlignmentType.CENTER,children:[new TextRun({text:"CÁLCULO E DETALHAMENTO",bold:true,size:52,color:ACC,font:"Calibri"})]}));
add(new Paragraph({spacing:{after:200},alignment:AlignmentType.CENTER,children:[new TextRun({text:"DA ARMADURA DE ESCADAS",bold:true,size:52,color:ACC,font:"Calibri"})]}));
add(new Paragraph({spacing:{after:1400},alignment:AlignmentType.CENTER,children:[new TextRun({text:"Apostila prática segundo a ABNT NBR 6118 e NBR 6120",size:26,color:"555555",font:"Calibri"})]}));
add(new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:"Escada de laje maciça · lance com patamar",size:22,color:"777777",font:"Calibri"})]}));
add(new Paragraph({children:[new PageBreak()]}));

// ---------- SUMARIO ----------
add(H("Sumário",HeadingLevel.HEADING_1));
add(new TableOfContents("Sumário",{hyperlink:true,headingStyleRange:"1-2"}));
add(new Paragraph({children:[new PageBreak()]}));

// ---------- COMO USAR ----------
add(H("Como usar esta apostila",HeadingLevel.HEADING_1));
add(P("Esta apostila acompanha o cálculo completo de uma escada de concreto armado, do lançamento da geometria até o desenho final da ferragem. Cada seção traz a teoria, a aplicação num exemplo numérico e o desenho correspondente."));
add(P("Sempre que aparecer mais de um formato possível de armadura, os dois são mostrados lado a lado, com as vantagens e desvantagens de cada um. A intenção é que você entenda que o cálculo permite mais de um caminho — e que a escolha entre eles é uma decisão de projeto e de obra, não uma regra fixa."));
add(P("Termos técnicos aparecem explicados entre parênteses na primeira vez que são usados."));

add(H("Dados do exemplo",HeadingLevel.HEADING_2));
add(table([
 ["Item","Valor"],
 ["Concreto","C25 (fck = 25 MPa)"],
 ["Aço","CA-50 (principal) e CA-60 (distribuição)"],
 ["Espessura da laje (h)","12 cm"],
 ["Cobrimento (c)","2,5 cm"],
 ["Altura útil (d)","9,0 cm"],
 ["Piso do degrau (s)","28 cm"],
 ["Espelho do degrau (e)","18,5 cm"],
 ["Largura do lance","121 cm"],
],[3200,5800]));

add(new Paragraph({children:[new PageBreak()]}));

// ---------- 1 ----------
add(H("1. Parâmetros de projeto",HeadingLevel.HEADING_1));
add(P("A geometria de uma escada nasce de dois números: o piso (s), que é a profundidade onde o pé apoia, e o espelho (e), que é a altura de cada degrau. Eles se relacionam pela fórmula de Blondel:"));
add(fml("s + 2e = 60 a 64 cm"));
add(P("Essa faixa garante um passo confortável. Fora dela, a escada fica cansativa (degraus curtos demais) ou perigosa (degraus longos demais)."));
add(P("Limites práticos adotados:",{bold:true}));
add(bullet("s ≥ 25 cm"));
add(bullet("e ≤ 19 cm"));
add(...img("fig/geometria.png",300,"Figura 1 — Geometria do lance: piso (s), espelho (e), inclinação (α), espessuras h, h₁ e hₘ, altura ℓv e projeção ℓh."));
add(H("1.1 Número de degraus e projeção",HeadingLevel.HEADING_2));
add(P("O número de degraus (n) sai da altura total a vencer dividida pelo espelho:"));
add(fml("e = ℓv / n"));
add(P("A projeção horizontal do lance usa (n − 1) degraus, porque o último degrau não soma piso — ele já é o patamar de chegada:"));
add(fml("ℓh = (n − 1) × s"));
add(H("1.2 Altura média da laje (hₘ)",HeadingLevel.HEADING_2));
add(P("A laje da escada é inclinada, então a espessura que interessa para o peso próprio não é h, mas a espessura média medida na vertical, considerando também os degraus:"));
add(fml("h₁ = h / cos(α)          hₘ = h₁ + e/2"));
add(P("No exemplo: α = arctan(18,5 / 28) ≈ 33,5°, resultando hₘ ≈ 24 cm."));

// ---------- 2 ----------
add(H("2. Ações (cargas)",HeadingLevel.HEADING_1));
add(H("2.1 Ações permanentes",HeadingLevel.HEADING_2));
add(P("São as cargas que ficam ali para sempre: o peso da própria estrutura e do que é fixo sobre ela."));
add(table([
 ["Carga","Expressão","Valor típico"],
 ["Peso próprio do lance","γconc × hₘ","25 kN/m³ × hₘ"],
 ["Peso próprio do patamar","γconc × h","25 kN/m³ × h"],
 ["Revestimento","conforme material","1,2 kN/m²"],
 ["Guarda-corpo","carga linear ÷ área de influência","conforme projeto"],
],[3000,3400,2600]));
add(P("O peso específico do concreto armado (25 kN/m³) e os pesos de revestimento vêm da NBR 6120, Tabelas 1 e 4.",{italics:true,size:19}));

add(H("2.2 Ações variáveis (carga acidental)",HeadingLevel.HEADING_2));
add(P("Esta é a carga de uso — o peso das pessoas e do que elas carregam. Não existe um valor único: ele depende de que tipo de edifício a escada atende. Os valores estão na NBR 6120, Tabela 10, na linha \"Escadas e passarelas\"."));
add(table([
 ["Uso da escada","Carga (kN/m²)"],
 ["Residencial ou hotel, dentro da unidade","2,5"],
 ["Residencial ou hotel, uso comum","3,0"],
 ["Hospitais","3,0"],
 ["Escolas","3,0"],
 ["Comercial, clubes, escritórios, bibliotecas","3,0"],
 ["Cinemas, centros comerciais, shopping","4,0"],
 ["Centros de exposição e de convenções","5,0"],
 ["Servindo arquibancada","5,0"],
 ["Com acesso público (caso geral)","3,0"],
 ["Sem acesso público (caso geral)","2,5"],
],[6400,2600]));
add(P("Verificação adicional exigida pela norma: em degraus isolados em balanço ou biapoiados, verificar separadamente uma carga concentrada de 2,5 kN na posição mais desfavorável — sem somar com a carga distribuída."));

add(H("2.3 Sobrecarga no patamar",HeadingLevel.HEADING_2));
add(P("Quando um lance se apoia diretamente no patamar (e não numa viga inclinada própria), o patamar recebe, além do seu próprio carregamento, a reação vertical desse lance. Essa reação entra como sobrecarga adicional:"));
add(fml("R = P.lance × ℓ.lance / 2"));
add(P("dividida pela área de influência do patamar para virar kN/m²."));
add(P("Isso não acontece quando o lance tem viga de apoio própria nas duas extremidades — nesse caso a carga vai direto para as vigas, sem passar pelo patamar.",{bold:true}));

// ---------- 3 ----------
add(H("3. Espessura da laje",HeadingLevel.HEADING_1));
add(P("Estimativa inicial a partir do vão:"));
add(fml("h = ℓ / 40"));
add(P("Mínimos exigidos pela NBR 6118:"));
add(table([
 ["Situação","Espessura mínima"],
 ["Laje de piso, não em balanço","8 cm"],
 ["Laje em balanço","10 cm"],
],[6000,3000]));
add(P("Em lajes em balanço, os esforços ainda devem ser majorados por γ = 1,95 − 0,05 × h."));
add(P("No exemplo adotou-se h = 12 cm, com folga sobre o mínimo de 8 cm."));

// ---------- 4 ----------
add(H("4. Esforços solicitantes",HeadingLevel.HEADING_1));
add(P("O lance é analisado como uma viga de 1 metro de largura (uma \"fatia\" da laje), apoiada conforme o esquema estrutural adotado. Com o carregamento distribuído da Seção 2, obtêm-se por equilíbrio os diagramas de momento fletor (M) e de força cortante (V)."));
add(P("No exemplo, o vão de cálculo do lance foi ℓ.lance = 196 + 28 = 224 cm, resultando:"));
add(fml("Mk = 23,93 kN·m        Md = Mk × 1,4 = 33,50 kN·m"));
add(P("O coeficiente γf = 1,4 majora o momento característico para o valor de cálculo — é a margem de segurança que a norma exige sobre as ações."));

// ---------- 5 ----------
add(H("5. Dimensionamento da armadura principal",HeadingLevel.HEADING_1));
add(H("5.1 Posição da linha neutra",HeadingLevel.HEADING_2));
add(P("A linha neutra é a fronteira dentro da seção: acima dela o concreto comprime, abaixo o aço traciona. Sua posição (x) define todo o resto do dimensionamento."));
add(fml("x = (d / λ) × [ 1 − √( 1 − Md / ( (αc/2) × bw × d² × fcd ) ) ]"));
add(P("Atenção: λ e αc não são constantes universais. Acima de 50 MPa eles mudam, e com eles mudam os números 1,25 e 0,425 que aparecem na versão simplificada da fórmula.",{bold:true}));
add(table([
 ["fck","λ","αc","1/λ","αc/2"],
 ["≤ 50 MPa","0,800","0,850","1,250","0,425"],
 ["60 MPa","0,775","0,808","1,290","0,404"],
 ["70 MPa","0,750","0,765","1,333","0,383"],
 ["80 MPa","0,725","0,723","1,379","0,362"],
 ["90 MPa","0,700","0,680","1,429","0,340"],
],[2200,1700,1700,1700,1700]));
add(P("No exemplo (C25, portanto ≤ 50 MPa): x = 1,25 × 9 × [1 − √(1 − 3350/6148)] = 3,66 cm."));

add(H("5.2 Verificação de ductilidade (Kx)",HeadingLevel.HEADING_2));
add(P("Ductilidade é a capacidade da peça de se deformar bastante antes de romper — de \"avisar\" que vai cair. O parâmetro que mede isso é Kx = x/d."));
add(fml("Kx = x / d = 3,66 / 9 = 0,407"));
add(...img("fig/dominios.png",470,"Figura 2 — Faixas de Kx e domínios de deformação."));
add(table([
 ["Domínio","Faixa de Kx","O que acontece"],
 ["2","Kx < 0,259","O aço se alonga muito antes do concreto esmagar. Muito seguro, pouco econômico."],
 ["3","0,259 a 0,45","O aço escoa e o concreto chega ao limite juntos. Faixa ideal."],
 ["4","Kx > 0,45","O concreto esmaga com o aço ainda elástico. Ruptura frágil, sem aviso. Proibido."],
],[1400,1900,5700]));
add(P("Para concretos acima de 50 MPa o limite cai de 0,45 para 0,35.",{bold:true}));
add(P("A verificação da deformação do aço confirma o domínio 3: εs = 3,5‰ × (d − x)/x = 5,11‰, menor que o limite de 10‰."));

add(H("5.3 Área de aço e escolha da bitola",HeadingLevel.HEADING_2));
add(fml("As = Md / [ fyd × (d − 0,4x) ] = 10,22 cm²/m"));
add(table([
 ["Bitola","Área da barra","Nº de barras/m","Espaçamento"],
 ["Ø10,0 mm","0,785 cm²","13,03","7,7 cm"],
 ["Ø12,5 mm","1,227 cm²","8,34","12,0 cm"],
],[2200,2400,2200,2200]));
add(P("Adotado: Ø10 mm c/ 7,5 cm, resultando As,ef = 10,47 cm²/m (maior que os 10,22 cm²/m necessários).",{bold:true}));
add(P("A armadura principal do patamar sai deste mesmo cálculo — mesma bitola e mesmo espaçamento — porque lance e patamar fazem parte do mesmo esquema estrutural. O que muda entre eles é apenas o formato e o comprimento da barra.",{bold:true}));

add(H("5.4 Tabela de áreas de aço",HeadingLevel.HEADING_2));
add(P("Bitolas e áreas conforme ABNT NBR 7480. Valores em cm²."));
add(table([
 ["Bitola","1","2","3","4","5","6","8","10"],
 ["Ø5,0","0,20","0,39","0,59","0,79","0,98","1,18","1,57","1,96"],
 ["Ø6,3","0,31","0,62","0,94","1,25","1,56","1,87","2,50","3,12"],
 ["Ø8,0","0,50","1,01","1,51","2,01","2,51","3,02","4,02","5,03"],
 ["Ø10,0","0,79","1,57","2,36","3,14","3,93","4,71","6,28","7,85"],
 ["Ø12,5","1,23","2,45","3,68","4,91","6,14","7,36","9,82","12,27"],
 ["Ø16,0","2,01","4,02","6,03","8,04","10,05","12,06","16,09","20,11"],
 ["Ø20,0","3,14","6,28","9,42","12,57","15,71","18,85","25,13","31,42"],
],[1400,950,950,950,950,950,950,950,950]));

add(H("5.5 Formatos possíveis da armadura principal",HeadingLevel.HEADING_2));
add(...img("fig/opcoes_principal.png",470,"Figura 3 — Três formatos válidos para a armadura principal."));
add(table([
 ["Opção","Quando usar","Observação"],
 ["A — ganchos em 90°","Falta comprimento reto para ancorar","O gancho reduz a ancoragem em 30% (α = 0,7)"],
 ["B — reta","Há espaço para o lb,nec inteiro","Mais barata: sem custo de dobra"],
 ["C — levantada (cavalete)","O momento inverte de sinal na dobra","A mesma barra atende tração inferior e superior"],
],[2400,3200,3400]));

// ---------- 6 ----------
add(H("6. Armadura secundária, de distribuição e de borda",HeadingLevel.HEADING_1));
add(H("6.1 Armadura mínima",HeadingLevel.HEADING_2));
add(fml("As,min = ρmin × h × bw = 0,0015 × 12 × 100 = 1,80 cm²/m"));
add(P("O ρmin de 0,15% vale até C30. Acima disso ele sobe: 0,179% em C40, 0,208% em C50, chegando a 0,256% em C90. Consulte sempre pelo fck exato.",{bold:true}));

add(H("6.2 Armadura de distribuição",HeadingLevel.HEADING_2));
add(P("Deve atender ao maior entre três critérios:"));
add(table([
 ["Critério","Valor"],
 ["20% da armadura principal","2,04 cm²/m"],
 ["50% da armadura mínima","0,90 cm²/m"],
 ["Valor absoluto mínimo","0,90 cm²/m"],
],[6000,3000]));
add(P("Governa 2,04 cm²/m. Adotado Ø6,3 mm c/ 15 cm (As,ef = 2,08 cm²/m). O espaçamento máximo para armadura secundária é 33 cm.",{bold:true}));

add(H("6.3 Armadura de borda",HeadingLevel.HEADING_2));
add(fml("As,borda = 0,67 × As,min = 1,21 cm²/m"));
add(P("Adotado Ø6,3 mm c/ 25 cm. Essa armadura deve se estender no mínimo 0,15 do vão menor da laje, medido a partir da face do apoio."));

add(H("6.4 Formatos possíveis",HeadingLevel.HEADING_2));
add(...img("fig/opcoes_secundaria.png",450,"Figura 4 — Formatos alternativos para distribuição e borda."));
add(table([
 ["Formato","Quando é boa escolha"],
 ["Distribuição reta","A barra morre dentro da laje, longe de borda livre. Mais simples e barata."],
 ["Distribuição com ganchos","A barra termina perto de borda livre e precisa de ancoragem num trecho curto."],
 ["Borda em L","Caso mais comum: há apoio de um lado. Gancho no apoio, ponta reta na laje."],
 ["Borda em grampo U","Borda livre nas duas faces (escada em balanço ou lateral exposta). Melhor contra fissura de canto."],
],[3000,6000]));

add(H("6.5 Resumo das armaduras",HeadingLevel.HEADING_2));
add(table([
 ["Função","Bitola","Espaçamento","As,ef"],
 ["Principal (lance e patamar)","Ø10,0","7,5 cm","10,47 cm²/m"],
 ["Distribuição","Ø6,3","15 cm","2,08 cm²/m"],
 ["Borda","Ø6,3","25 cm","1,25 cm²/m"],
],[3300,1900,1900,1900]));

// ---------- 7 ----------
add(H("7. Ancoragem das barras",HeadingLevel.HEADING_1));
add(P("Ancorar é garantir que a barra não escorregue dentro do concreto quando tracionada. A força passa do aço para o concreto por aderência (o atrito e o encaixe das nervuras da barra), e isso exige um comprimento mínimo."));
add(H("7.1 Resistência de aderência",HeadingLevel.HEADING_2));
add(fml("fctd = 0,21 × ∛(fck²) / γc          fbd = η1 × η2 × η3 × fctd"));
add(table([
 ["Coeficiente","Valor","Condição"],
 ["η1","1,00","Barras lisas (CA-25, CA-60)"],
 ["η1","2,25","Barras nervuradas (CA-50)"],
 ["η2","1,00","Boa aderência"],
 ["η2","0,70","Má aderência"],
 ["η3","1,00","φ < 32 mm"],
 ["η3","(132 − φ)/100","φ > 32 mm (φ em mm)"],
],[2200,2200,4600]));
add(P("No exemplo: fctd = 0,1282 kN/cm² e fbd = 2,25 × 0,1282 = 0,2886 kN/cm²."));
add(P("Cuidado: fctd e fbd são grandezas diferentes. Usar o fctd direto no lugar do fbd faz o comprimento de ancoragem sair 2,25 vezes maior que o correto.",{bold:true}));

add(H("7.2 Comprimentos de ancoragem",HeadingLevel.HEADING_2));
add(fml("lb = (φ/4) × (fyd / fbd) = 37,7 cm ≈ 38φ"));
add(fml("lb,nec = α × lb × (As,calc / As,ef) ≥ lb,min"));
add(table([
 ["Situação","α","lb,nec"],
 ["Barra reta","1,0","36,8 cm"],
 ["Barra com gancho","0,7","25,7 cm"],
],[4000,2000,3000]));
add(P("lb,min é o maior entre 0,3·lb (11,3 cm), 10φ (10 cm) e 10 cm — atendido nos dois casos."));

add(H("7.3 Quando usar gancho",HeadingLevel.HEADING_2));
add(table([
 ["Situação","Gancho"],
 ["Barras lisas","Obrigatório"],
 ["Barras com alternância de tração e compressão","Sem gancho"],
 ["Demais casos","Com ou sem gancho"],
 ["φ > 32 mm ou feixes de barras","Não recomendado"],
 ["Barras comprimidas","Nunca com gancho"],
],[6000,3000]));

add(H("7.4 Tabelas de gancho e dobra",HeadingLevel.HEADING_2));
add(P("Tabela A — Ganchos da armadura longitudinal tracionada",{bold:true}));
add(table([
 ["Tipo de gancho","Ângulo","Ponta reta mínima"],
 ["Semicircular","180°","2φ"],
 ["Em ângulo de 45° (interno)","45°","4φ"],
 ["Em ângulo reto","90°","8φ"],
],[4200,2200,2600]));
add(P("Exemplo: barra Ø10 mm com gancho de 90° exige 8 × 10 = 80 mm = 8 cm de ponta reta.",{italics:true,size:19}));

add(P("Tabela B — Diâmetro do pino de dobramento (armadura longitudinal)",{bold:true,before:160}));
add(table([
 ["Bitola","CA-25","CA-50","CA-60"],
 ["φ < 20 mm","4φ","5φ","6φ"],
 ["φ ≥ 20 mm","5φ","8φ","—"],
],[3000,2000,2000,2000]));
add(P("O pino de dobramento é o cilindro em volta do qual o armador dobra a barra na bancada. Se for fino demais, a barra aperta o concreto na curva e pode causar fendilhamento (o concreto abrindo em fatias).",{size:19}));

add(P("Tabela C — Ganchos de estribo",{bold:true,before:160}));
add(table([
 ["Tipo","Ponta reta mínima"],
 ["Semicircular ou 45°","5φt, nunca menor que 5 cm"],
 ["Em ângulo reto (90°)","10φt, nunca menor que 7 cm"],
],[4200,4800]));
add(P("O gancho reto de 90° não pode ser usado em barras lisas. A norma prefere o gancho de 135° voltado para dentro da peça.",{size:19}));

add(P("Tabela D — Diâmetro do pino de dobramento (estribos)",{bold:true,before:160}));
add(table([
 ["Bitola do estribo","D mínimo"],
 ["≤ 10 mm","3φt"],
 ["12,5 e 16 mm","4φt"],
 ["≥ 20 mm","5φt"],
],[4500,4500]));

// ---------- 8 ----------
add(H("8. Comprimento das barras",HeadingLevel.HEADING_1));
add(H("8.1 De onde sai cada parcela",HeadingLevel.HEADING_2));
add(...img("fig/anatomia.png",450,"Figura 5 — Composição do comprimento de uma barra com gancho."));
add(P("O trecho reto tem duas origens possíveis:"));
add(bullet("Cobrindo um vão — é a distância entre apoios menos os cobrimentos. Vem da geometria da escada. Exemplo: 242 − 2c = 237 cm."));
add(bullet("Ancorando — é o lb,nec calculado na Seção 7. Vem da aderência entre aço e concreto."));
add(P("Muitas barras somam os dois: um trecho que atravessa o vão mais um trecho de ancoragem em cada ponta onde emenda com a barra vizinha."));
add(P("O gancho (Δlg) no exemplo vale h − 2c = 12 − 5 = 7 cm. Repare que isso não é o 8φ da norma — é um limite geométrico: a dobra precisa caber dentro da espessura da laje, descontados os cobrimentos.",{bold:true}));
add(P("Este é o ponto que mais confunde: o 8φ é o mínimo que a norma exige; o h − 2c é o máximo que a peça permite. Se o máximo físico for menor que o mínimo normativo (como aqui, 7 cm contra 8 cm), é sinal de que a laje está fina para aquele gancho — aumente h, reduza a bitola ou mude para gancho semicircular, que exige apenas 2φ."));
add(P("Observação prática: a barra dobrada fica ligeiramente mais curta que a soma dos trechos desenhados, porque ela não dobra em canto vivo — faz uma curva com raio. Registre o comprimento no eixo da barra; o corte real terá esse pequeno desconto.",{size:19,italics:true}));

add(H("8.2 Quantidade de barras",HeadingLevel.HEADING_2));
add(fml("n = b / s"));
add(P("onde b é a largura livre do vão medida perpendicularmente à direção das barras, e s o espaçamento. O resultado é sempre arredondado para cima."));
add(table([
 ["Trecho","Cálculo","Quantidade"],
 ["Principal do patamar","121 / 7,5","16 Ø10"],
 ["Principal do lance","121 / 7,5","16 Ø10"],
 ["Distribuição do patamar","120 / 15","8 Ø6,3"],
 ["Distribuição do lance","(196 + 28) / 15","15 Ø6,3"],
 ["Reforço da divisa","—","1 Ø10"],
 ["Ancoragem dos cantos","2 por canto","4 Ø6,3"],
],[3400,3000,2600]));

// ---------- 9 ----------
add(H("9. Detalhamento",HeadingLevel.HEADING_1));
add(H("9.1 Identificação das posições",HeadingLevel.HEADING_2));
add(P("Toda posição vem sempre acompanhada da descrição do que ela é — no desenho, na tabela e no texto. Assim ninguém precisa decorar a numeração."));
add(table([
 ["Pos.","Bitola","Formato","O que é"],
 ["N1","Ø10","1 gancho","Armadura principal do patamar, face inferior"],
 ["N2","Ø10","1 gancho","Armadura principal do lance, face inferior"],
 ["N3","Ø10","2 ganchos","Armadura principal do lance superior, face inferior"],
 ["N4","Ø6,3","Reta","Armadura de distribuição, patamar e lance"],
 ["N5","Ø10","Reta","Reforço na divisa entre patamar e lance"],
 ["N6","Ø6,3","Reta","Ancoragem dos cantos reentrantes (2 por canto)"],
],[900,1100,1600,5400]));
add(...img("fig/formatos_n.png",450,"Figura 6 — Formatos das barras, desenhadas separadamente."));

add(new Paragraph({children:[new PageBreak()]}));
add(H("9.2 Corte da escada com as armaduras",HeadingLevel.HEADING_2));
add(...img("fig/corte_conjunto.png",620,"Figura 7 — Corte longitudinal com todas as posições. N4, N5 e N6 aparecem como pontos porque correm perpendiculares ao papel."));

add(H("9.3 Vistas separadas",HeadingLevel.HEADING_2));
add(P("Separar as armaduras em desenhos distintos ajuda muito a entender o que cada uma faz. Abaixo, a mesma região vista de cima, primeiro só com as principais e depois só com as secundárias."));
add(...img("fig/vista_principais.png",380,"Figura 8 — Somente a armadura principal. Corre no sentido da subida e resiste ao momento fletor."));
add(...img("fig/vista_secundarias.png",380,"Figura 9 — Somente a armadura de distribuição. Atravessa a largura, distribui as cargas e controla a fissuração."));
add(P("Sobrepondo as duas mentalmente, você tem a malha completa. A armadura de distribuição fica sempre por cima da principal na face inferior — quem precisa ficar o mais longe possível da linha neutra é a principal."));

add(new Paragraph({children:[new PageBreak()]}));
add(H("9.4 Ancoragem dos cantos reentrantes",HeadingLevel.HEADING_2));
add(P("Canto reentrante é o vértice que \"entra\" para dentro da peça — no encontro do lance com o patamar. Quando a armadura principal dobra ali, as forças de tração das duas pernas da barra geram uma resultante que aponta para fora, na direção do cobrimento. Essa resultante tende a arrancar a camada de concreto e empurrar a barra para fora da peça."));
add(...img("fig/canto.png",560,"Figura 10 — Mecanismo do canto reentrante e as duas barras de ancoragem."));
add(P("A solução é atravessar duas barras nesse vértice, segurando a armadura principal contra essa força. São as barras N6."));
add(P("Existem dois cantos reentrantes na escada: um no encontro do patamar inferior com o lance, e outro no encontro do lance com o patamar superior. Os dois precisam das barras de ancoragem.",{bold:true}));
add(table([
 ["Solução","Vantagem","Desvantagem"],
 ["Barra dobrada + 2 barras de ancoragem (N6)","Menos peças, mais simples de montar","Depende do posicionamento correto das transversais"],
 ["Barras cruzadas no vértice","Elimina a força de arrancamento na origem","Mais aço, mais corte e amarração"],
],[3000,3000,3000]));

add(H("9.5 Ideia construtiva: dividir a N2",HeadingLevel.HEADING_2));
add(P("A N2 pode ser executada de duas maneiras. Nenhuma delas está errada — a escolha é de detalhamento, não de cálculo."));
add(...img("fig/n2_dividida.png",600,"Figura 11 — A N2 dividida em arranque (N2a) e barra do lance (N2b), unidas por traspasse."));
add(table([
 ["","Opção 1 — barra inteira","Opção 2 — arranque + emenda"],
 ["Peças","1 barra longa","2 barras (N2a + N2b)"],
 ["Vantagem","Menos emendas, menos aço de traspasse","Muito mais fácil de posicionar em obra"],
 ["Desvantagem","Difícil enfiar dentro do patamar; esbarra na fôrma e nos arranques de pilar","Gasta o comprimento extra do traspasse"],
 ["Quando usar","Patamares curtos, armadura pouco congestionada","O caso mais comum na prática"],
],[1800,3600,3600]));
add(P("A Opção 2 é uma melhoria construtiva: não corrige nenhum erro de cálculo, mas facilita bastante a montagem da ferragem. É o tipo de coisa que não se aprende no cálculo e se descobre no canteiro."));
add(P("Regra do traspasse:",{bold:true,before:160}));
add(bullet("A sobreposição deve ter no mínimo o lb,nec (25,7 cm no exemplo). É por esse trecho que a força passa de uma barra para a outra, através do concreto."));
add(bullet("A emenda deve ficar fora do ponto de momento máximo — leve-a para uma região de esforço menor."));
add(bullet("Emendas de barras vizinhas devem ser escalonadas, nunca todas no mesmo ponto, para não criar uma seção enfraquecida."));

add(new Paragraph({children:[new PageBreak()]}));
add(H("10. Quadro resumo de ferro",HeadingLevel.HEADING_1));
add(table([
 ["Pos.","Bitola","Qtd.","Formato","Função"],
 ["N1","Ø10,0","16","1 gancho","Principal do patamar"],
 ["N2","Ø10,0","16","1 gancho","Principal do lance"],
 ["N3","Ø10,0","16","2 ganchos","Principal do lance superior"],
 ["N4","Ø6,3","23","Reta","Distribuição (8 patamar + 15 lance)"],
 ["N5","Ø10,0","1","Reta","Reforço da divisa patamar/lance"],
 ["N6","Ø6,3","4","Reta","Ancoragem dos cantos (2 por canto)"],
],[800,1300,900,1700,4300]));

add(H("Normas de referência",HeadingLevel.HEADING_1));
add(bullet("ABNT NBR 6118 — Projeto de estruturas de concreto: dimensionamento, domínios, ancoragem, ganchos e dobras."));
add(bullet("ABNT NBR 6120 — Ações para o cálculo de estruturas de edificações: pesos específicos e cargas de utilização."));
add(bullet("ABNT NBR 7480 — Barras e fios de aço para armaduras: bitolas, áreas e massas nominais."));

const doc=new Document({
 creator:"Apostila de escadas",title:"Cálculo e detalhamento da armadura de escadas",
 styles:{default:{document:{run:{font:"Calibri",size:22}}}},
 sections:[{properties:{page:{margin:{top:1000,bottom:1000,left:1100,right:1100}}},
  footers:{default:new Footer({children:[new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({children:[PageNumber.CURRENT],size:18,color:"888888"})]})]})},
  children:K}]});

Packer.toBuffer(doc).then(b=>{fs.writeFileSync("/mnt/user-data/outputs/Apostila_Armadura_Escadas.docx",b);console.log("docx ok",b.length);});
