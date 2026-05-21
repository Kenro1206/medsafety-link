const pptxgen = require("pptxgenjs");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "MedSafety Link";
pptx.subject = "Clinician-friendly introduction to MedSafety Link";
pptx.title = "MedSafety Link 日本糖尿病学会紹介用スライド";
pptx.company = "Kumamoto Chuo Hospital";
pptx.lang = "ja-JP";
pptx.theme = {
  headFontFace: "Yu Gothic",
  bodyFontFace: "Yu Gothic",
  lang: "ja-JP",
};
pptx.defineLayout({ name: "LAYOUT_WIDE", width: 13.333, height: 7.5 });
pptx.layout = "LAYOUT_WIDE";

const C = {
  navy: "132033",
  blue: "176B9A",
  blue2: "2F6FE4",
  teal: "237B75",
  green: "1F8A64",
  mint: "EAF6F3",
  mint2: "DFF4ED",
  red: "C9342D",
  orange: "E18B2D",
  yellow: "FFF3CD",
  gray: "64748B",
  light: "F7FAFC",
  white: "FFFFFF",
  line: "DCE6EF",
  paleBlue: "EAF2FF",
};

const font = "Yu Gothic";

function bg(slide, color = C.light) {
  slide.background = { color };
}

function topbar(slide, section, n) {
  slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 0.16, fill: { color: C.blue }, line: { color: C.blue } });
  slide.addText(section, { x: 0.45, y: 0.31, w: 8.4, h: 0.22, fontFace: font, fontSize: 8.4, bold: true, color: C.gray, margin: 0 });
  slide.addText(String(n).padStart(2, "0"), { x: 12.1, y: 0.29, w: 0.55, h: 0.22, fontFace: font, fontSize: 8.8, bold: true, color: C.gray, align: "right", margin: 0 });
}

function title(slide, main, sub) {
  slide.addText(main, { x: 0.65, y: 0.78, w: 11.7, h: 0.65, fontFace: font, fontSize: 25, bold: true, color: C.navy, fit: "shrink", margin: 0 });
  if (sub) slide.addText(sub, { x: 0.68, y: 1.45, w: 10.9, h: 0.24, fontFace: font, fontSize: 10.5, color: C.gray, margin: 0 });
}

function card(slide, x, y, w, h, fill = C.white, line = C.line) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.08,
    fill: { color: fill },
    line: { color: line, width: 1 },
    shadow: { type: "outer", color: "AAB4BF", opacity: 0.11, blur: 1, angle: 45, distance: 1 },
  });
}

function pill(slide, text, x, y, w, fill = C.mint2, color = C.teal, fs = 9) {
  slide.addShape(pptx.ShapeType.roundRect, { x, y, w, h: 0.34, rectRadius: 0.08, fill: { color: fill }, line: { color: fill } });
  slide.addText(text, { x: x + 0.07, y: y + 0.075, w: w - 0.14, h: 0.15, fontFace: font, fontSize: fs, bold: true, color, align: "center", margin: 0 });
}

function bigNumber(slide, num, x, y, color) {
  slide.addShape(pptx.ShapeType.ellipse, { x, y, w: 0.72, h: 0.72, fill: { color }, line: { color } });
  slide.addText(String(num), { x, y: y + 0.2, w: 0.72, h: 0.15, fontFace: font, fontSize: 13, bold: true, color: C.white, align: "center", margin: 0 });
}

function arrow(slide, x1, y1, x2, y2, color = C.blue) {
  slide.addShape(pptx.ShapeType.line, { x: x1, y: y1, w: x2 - x1, h: y2 - y1, line: { color, width: 2.2, endArrowType: "triangle" } });
}

function phone(slide, x, y, w, h, variant = "safety") {
  slide.addShape(pptx.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.18, fill: { color: "111827" }, line: { color: "111827" } });
  slide.addShape(pptx.ShapeType.roundRect, { x: x + 0.12, y: y + 0.12, w: w - 0.24, h: h - 0.24, rectRadius: 0.12, fill: { color: "EEF7F4" }, line: { color: "EEF7F4" } });
  slide.addText("患者さんのLINE", { x: x + 0.28, y: y + 0.32, w: w - 0.56, h: 0.18, fontFace: font, fontSize: 8.5, bold: true, color: C.teal, margin: 0 });
  card(slide, x + 0.33, y + 0.72, w - 0.66, 1.42, C.white, C.white);
  const msg = variant === "photo"
    ? "足の状態が心配な場合は、写真を送ってください。"
    : "【安否確認】現在の状況を選んでください。";
  slide.addText(msg, { x: x + 0.48, y: y + 0.88, w: w - 0.96, h: 0.32, fontFace: font, fontSize: 8.2, color: C.navy, margin: 0, fit: "shrink" });
  const labels = variant === "photo" ? ["写真を送信", "痛みあり", "赤みあり", "至急相談"] : ["無事", "体調不良", "薬不足", "至急連絡"];
  labels.forEach((t, i) => pill(slide, t, x + 0.48 + (i % 2) * 1.28, y + 1.33 + Math.floor(i / 2) * 0.36, 1.08, C.mint2, C.teal, 7.2));
  card(slide, x + 0.33, y + 2.42, w - 0.66, 0.62, C.white, C.white);
  slide.addText("ボタンを押すだけで回答完了", { x: x + 0.48, y: y + 2.64, w: w - 0.96, h: 0.14, fontFace: font, fontSize: 7.8, color: C.gray, align: "center", margin: 0 });
}

function miniDashboard(slide, x, y, w, h) {
  card(slide, x, y, w, h, C.white);
  slide.addText("医療者画面", { x: x + 0.25, y: y + 0.18, w: w - 0.5, h: 0.22, fontFace: font, fontSize: 11, bold: true, color: C.blue, margin: 0 });
  const metrics = [["回答済", "86", C.green], ["未回答", "34", C.orange], ["要対応", "3", C.red]];
  metrics.forEach((m, i) => {
    const mx = x + 0.28 + i * ((w - 0.7) / 3);
    card(slide, mx, y + 0.7, (w - 1.0) / 3, 0.92, i === 2 ? "FFF4F2" : "FBFDFF", i === 2 ? "F1BBB8" : C.line);
    slide.addText(m[0], { x: mx + 0.1, y: y + 0.84, w: (w - 1.2) / 3, h: 0.14, fontFace: font, fontSize: 7.2, bold: true, color: C.gray, align: "center", margin: 0 });
    slide.addText(m[1], { x: mx + 0.1, y: y + 1.08, w: (w - 1.2) / 3, h: 0.26, fontFace: font, fontSize: 20, bold: true, color: m[2], align: "center", margin: 0 });
  });
  slide.addShape(pptx.ShapeType.roundRect, { x: x + 0.35, y: y + 2.0, w: w - 0.7, h: 0.5, rectRadius: 0.06, fill: { color: "FFF4F2" }, line: { color: "F1BBB8" } });
  slide.addText("重症アラートを上に表示", { x: x + 0.55, y: y + 2.16, w: w - 1.1, h: 0.14, fontFace: font, fontSize: 8.5, bold: true, color: C.red, align: "center", margin: 0 });
}

function slide1() {
  const s = pptx.addSlide(); bg(s, C.blue);
  s.addShape(pptx.ShapeType.rect, { x: 8.35, y: 0, w: 5.0, h: 7.5, fill: { color: C.teal, transparency: 8 }, line: { color: C.teal, transparency: 100 } });
  s.addText("日本糖尿病学会年次学術集会 紹介用", { x: 0.65, y: 0.55, w: 5.2, h: 0.24, fontFace: font, fontSize: 10.5, bold: true, color: "EAF4F7", margin: 0 });
  s.addText("ICTが得意でなくても\\n患者さんとつながれる", { x: 0.65, y: 1.35, w: 7.7, h: 1.25, fontFace: font, fontSize: 34, bold: true, color: C.white, margin: 0, fit: "shrink" });
  s.addText("LINEを使った安否・症状確認システム\\nMedSafety Link", { x: 0.68, y: 3.05, w: 6.7, h: 0.58, fontFace: font, fontSize: 17, bold: true, color: "DFF4ED", margin: 0 });
  phone(s, 9.1, 0.95, 2.75, 4.0);
  miniDashboard(s, 6.05, 4.65, 5.95, 2.15);
  s.addText("熊本中央病院 糖尿病・内分泌・代謝内科　西田 健朗", { x: 0.68, y: 6.72, w: 6.5, h: 0.2, fontFace: font, fontSize: 9.3, color: C.white, margin: 0 });
}

function slide2() {
  const s = pptx.addSlide(); bg(s); topbar(s, "まず伝えたいこと", 2);
  title(s, "これは“難しいICTシステム”ではなく、LINEで患者さんの状況を見る仕組みです", "患者さん側は普段のLINE、医療者側は一覧画面を見るだけ");
  const cards = [
    ["患者さん", "LINEに届いた質問に\\nボタンで回答", C.teal],
    ["医療者", "回答済・未回答・要対応を\\n一覧で確認", C.blue],
    ["管理者", "患者登録と送信履歴を\\n画面で管理", C.orange],
  ];
  cards.forEach((c, i) => {
    const x = 0.85 + i * 4.05;
    card(s, x, 2.05, 3.45, 3.15, C.white);
    s.addShape(pptx.ShapeType.ellipse, { x: x + 1.28, y: 2.38, w: 0.88, h: 0.88, fill: { color: c[2] }, line: { color: c[2] } });
    s.addText(c[0], { x: x + 0.35, y: 3.55, w: 2.75, h: 0.3, fontFace: font, fontSize: 18, bold: true, color: c[2], align: "center", margin: 0 });
    s.addText(c[1], { x: x + 0.35, y: 4.08, w: 2.75, h: 0.6, fontFace: font, fontSize: 14.5, bold: true, color: C.navy, align: "center", margin: 0, fit: "shrink" });
  });
  s.addText("ポイント: 患者さんにも医療者にも、新しい専用アプリを覚えてもらわない", { x: 1.05, y: 6.18, w: 11.2, h: 0.3, fontFace: font, fontSize: 16.5, bold: true, color: C.green, align: "center", margin: 0 });
}

function slide3() {
  const s = pptx.addSlide(); bg(s); topbar(s, "現場の困りごと", 3);
  title(s, "災害時・時間外・電話集中時に、全員へ電話するのは難しい", "必要なのは、全員に同じ手間をかけることではなく、要対応者を早く見つけること");
  const problems = [
    ["電話がつながらない", "災害時や時間外は電話が集中し、安否確認が進みにくい"],
    ["誰が未回答か分からない", "紙や個別メモでは、全体像の把握に時間がかかる"],
    ["要対応者を見落としやすい", "低血糖、薬剤不足、通院困難などを優先したい"],
  ];
  problems.forEach((p, i) => {
    const y = 1.85 + i * 1.35;
    card(s, 1.0, y, 11.3, 1.0, i === 1 ? C.white : C.mint);
    bigNumber(s, i + 1, 1.28, y + 0.14, [C.red, C.orange, C.blue][i]);
    s.addText(p[0], { x: 2.18, y: y + 0.18, w: 3.0, h: 0.25, fontFace: font, fontSize: 14.5, bold: true, color: C.navy, margin: 0 });
    s.addText(p[1], { x: 5.15, y: y + 0.18, w: 6.5, h: 0.3, fontFace: font, fontSize: 12, color: C.gray, margin: 0, fit: "shrink" });
  });
}

function slide4() {
  const s = pptx.addSlide(); bg(s); topbar(s, "患者さん側", 4);
  title(s, "患者さんは、LINEで届いたメッセージにボタンで答えるだけ", "高齢者やICTに不慣れな患者さんにも説明しやすい");
  phone(s, 1.05, 1.55, 3.2, 4.6);
  const explains = [
    ["1", "友だち追加", "QRコードからLINE公式アカウントを追加"],
    ["2", "メッセージ受信", "安否確認や症状確認がLINEに届く"],
    ["3", "ボタン回答", "文字入力が苦手でも状況を伝えられる"],
    ["4", "必要時だけ追加", "写真や位置情報も送れる"],
  ];
  explains.forEach((e, i) => {
    const x = 5.05 + (i % 2) * 3.45;
    const y = 1.85 + Math.floor(i / 2) * 1.55;
    card(s, x, y, 3.05, 1.05, C.white);
    bigNumber(s, e[0], x + 0.18, y + 0.17, i % 2 ? C.teal : C.blue);
    s.addText(e[1], { x: x + 0.95, y: y + 0.18, w: 1.85, h: 0.22, fontFace: font, fontSize: 13, bold: true, color: C.navy, margin: 0 });
    s.addText(e[2], { x: x + 0.95, y: y + 0.52, w: 1.85, h: 0.25, fontFace: font, fontSize: 8.8, color: C.gray, margin: 0, fit: "shrink" });
  });
  s.addText("緊急時はLINEではなく、電話・救急外来受診を案内", { x: 5.15, y: 5.55, w: 6.55, h: 0.28, fontFace: font, fontSize: 15.5, bold: true, color: C.red, align: "center", margin: 0 });
}

function slide5() {
  const s = pptx.addSlide(); bg(s); topbar(s, "医療者側", 5);
  title(s, "医療者は、ダッシュボードで“対応が必要な人”から見る", "回答済・未回答・緊急未対応を一画面で確認");
  miniDashboard(s, 0.9, 1.55, 5.6, 3.8);
  const views = [
    ["未回答再送", "返事がない患者さんに再送"],
    ["重症アラート", "低血糖・薬剤不足・至急連絡希望を上に表示"],
    ["個別送信", "必要な患者さんへ個別に連絡"],
    ["履歴保存", "誰に何を送ったか、どんな回答かを記録"],
  ];
  views.forEach((v, i) => {
    const y = 1.65 + i * 0.95;
    card(s, 7.0, y, 5.45, 0.72, i % 2 ? C.white : C.mint);
    s.addText(v[0], { x: 7.25, y: y + 0.16, w: 1.5, h: 0.16, fontFace: font, fontSize: 11.5, bold: true, color: C.blue, margin: 0 });
    s.addText(v[1], { x: 8.75, y: y + 0.15, w: 3.35, h: 0.18, fontFace: font, fontSize: 9.4, color: C.navy, margin: 0, fit: "shrink" });
  });
}

function slide6() {
  const s = pptx.addSlide(); bg(s); topbar(s, "災害時の使い方", 6);
  title(s, "災害時は、電話を始める前に全体状況をつかむ", "LINEで一次スクリーニングし、電話や受診調整は必要な患者さんへ集中");
  const steps = [
    ["1", "対象患者へ\\n一斉送信", C.blue],
    ["2", "患者さんが\\nボタンで回答", C.teal],
    ["3", "未回答・重症を\\n自動で一覧化", C.orange],
    ["4", "要対応者へ\\n電話・個別連絡", C.red],
  ];
  steps.forEach((st, i) => {
    const x = 0.9 + i * 3.0;
    card(s, x, 2.15, 2.55, 2.35, C.white);
    bigNumber(s, st[0], x + 0.92, 2.48, st[2]);
    s.addText(st[1], { x: x + 0.35, y: 3.4, w: 1.85, h: 0.48, fontFace: font, fontSize: 14, bold: true, color: C.navy, align: "center", margin: 0, fit: "shrink" });
    if (i < 3) arrow(s, x + 2.62, 3.28, x + 2.95, 3.28, C.teal);
  });
  s.addText("目的: 全員に電話する前に、誰が無事で、誰に対応が必要かを見える化する", { x: 1.0, y: 5.75, w: 11.3, h: 0.32, fontFace: font, fontSize: 16.5, bold: true, color: C.green, align: "center", margin: 0 });
}

function slide7() {
  const s = pptx.addSlide(); bg(s); topbar(s, "通常診療での使い方", 7);
  title(s, "災害時だけでなく、日常診療のフォローにも使える", "1型糖尿病・透析・足病変など、目的別に文面とボタンを切り替え");
  const areas = [
    ["1型糖尿病", "低血糖が心配\\n薬・インスリン不足\\n至急連絡希望", C.blue],
    ["透析患者", "透析に行けない\\nシャントが心配\\n体調不良", C.teal],
    ["足病変", "写真を送信\\n痛み・赤み\\n発熱・悪化", C.orange],
  ];
  areas.forEach((a, i) => {
    const x = 0.85 + i * 4.05;
    card(s, x, 2.0, 3.45, 3.35, C.white);
    s.addText(a[0], { x: x + 0.25, y: 2.3, w: 2.95, h: 0.3, fontFace: font, fontSize: 17, bold: true, color: a[2], align: "center", margin: 0 });
    a[1].split("\\n").forEach((line, j) => pill(s, line, x + 0.52, 3.05 + j * 0.55, 2.4, j % 2 ? C.mint : C.mint2, C.navy, 9.6));
  });
  s.addText("現場ごとの言葉で送れるため、患者さんにも伝わりやすい", { x: 1.0, y: 6.1, w: 11.2, h: 0.3, fontFace: font, fontSize: 16, bold: true, color: C.green, align: "center", margin: 0 });
}

function slide8() {
  const s = pptx.addSlide(); bg(s); topbar(s, "写真・位置情報", 8);
  title(s, "写真や位置情報も、必要な時だけ受け取れる", "足病変や災害時の所在確認など、電話では伝わりにくい情報を補える");
  phone(s, 0.95, 1.55, 3.1, 4.55, "photo");
  card(s, 5.05, 1.85, 3.0, 2.0, C.white);
  s.addText("写真", { x: 5.3, y: 2.12, w: 2.5, h: 0.28, fontFace: font, fontSize: 18, bold: true, color: C.orange, align: "center", margin: 0 });
  s.addText("足病変の状態を\\n管理画面から確認", { x: 5.35, y: 2.85, w: 2.4, h: 0.45, fontFace: font, fontSize: 14, bold: true, color: C.navy, align: "center", margin: 0, fit: "shrink" });
  card(s, 8.55, 1.85, 3.0, 2.0, C.white);
  s.addText("位置情報", { x: 8.8, y: 2.12, w: 2.5, h: 0.28, fontFace: font, fontSize: 18, bold: true, color: C.teal, align: "center", margin: 0 });
  s.addText("災害時の所在を\\n地図リンクで確認", { x: 8.85, y: 2.85, w: 2.4, h: 0.45, fontFace: font, fontSize: 14, bold: true, color: C.navy, align: "center", margin: 0, fit: "shrink" });
  card(s, 5.3, 4.65, 6.0, 0.75, C.yellow, "F1D58A");
  s.addText("注意: 緊急対応そのものはLINEではなく、電話・救急外来へ誘導", { x: 5.55, y: 4.9, w: 5.5, h: 0.18, fontFace: font, fontSize: 10.8, bold: true, color: C.navy, align: "center", margin: 0 });
}

function slide9() {
  const s = pptx.addSlide(); bg(s); topbar(s, "導入しやすさ", 9);
  title(s, "施設ごとに設定でき、難しい操作は画面内に案内を表示", "新しい施設でも、設定画面から必要事項を確認できる");
  const setup = [
    ["施設ID", "ログインと設定を施設ごとに分ける"],
    ["LINE設定", "Webhook URL、アクセストークン、接続診断"],
    ["Google設定", "Sheets、Drive、共有先メールを案内"],
    ["マニュアル", "患者登録、送信、トラブル対応をサイト内に掲載"],
  ];
  setup.forEach((s2, i) => {
    const x = 0.9 + (i % 2) * 6.0;
    const y = 1.9 + Math.floor(i / 2) * 1.55;
    card(s, x, y, 5.35, 1.1, i % 2 ? C.white : C.mint);
    s.addText(s2[0], { x: x + 0.25, y: y + 0.22, w: 1.65, h: 0.24, fontFace: font, fontSize: 13.5, bold: true, color: C.blue, margin: 0 });
    s.addText(s2[1], { x: x + 1.95, y: y + 0.24, w: 3.1, h: 0.23, fontFace: font, fontSize: 10.3, color: C.navy, margin: 0, fit: "shrink" });
  });
  s.addText("ICT担当者だけでなく、診療科スタッフが運用イメージを理解しやすい設計", { x: 1.0, y: 5.75, w: 11.2, h: 0.32, fontFace: font, fontSize: 15.5, bold: true, color: C.green, align: "center", margin: 0 });
}

function slide10() {
  const s = pptx.addSlide(); bg(s); topbar(s, "先生方へのメッセージ", 10);
  title(s, "まずは小さく試せる：スタッフデモから患者登録へ", "全患者一斉導入ではなく、対象を絞って運用を確認する");
  const phases = [
    ["Step 1", "院内スタッフでLINE回答を体験"],
    ["Step 2", "患者10〜20名で小規模運用"],
    ["Step 3", "災害訓練・通常フォローで検証"],
    ["Step 4", "対象疾患・施設を拡大"],
  ];
  phases.forEach((p, i) => {
    const y = 1.85 + i * 0.95;
    card(s, 1.25, y, 10.8, 0.68, C.white);
    pill(s, p[0], 1.5, y + 0.17, 1.15, i % 2 ? C.mint : C.mint2, i % 2 ? C.blue : C.green, 8.5);
    s.addText(p[1], { x: 3.0, y: y + 0.18, w: 8.4, h: 0.18, fontFace: font, fontSize: 13, bold: true, color: C.navy, margin: 0 });
  });
  s.addText("評価指標: 返信率、未回答率、要対応者確認までの時間、電話件数、スタッフ負担", { x: 1.0, y: 6.0, w: 11.2, h: 0.28, fontFace: font, fontSize: 13.8, bold: true, color: C.blue, align: "center", margin: 0 });
}

function slide11() {
  const s = pptx.addSlide(); bg(s, C.navy);
  s.addText("まとめ", { x: 0.75, y: 0.65, w: 1.4, h: 0.3, fontFace: font, fontSize: 17, bold: true, color: C.white, margin: 0 });
  s.addText("MedSafety Linkは、糖尿病診療の現場で\\n「患者さんに聞く」「一覧で見る」「必要な人から対応する」\\nをLINEで支援する仕組みです。", {
    x: 0.9, y: 1.55, w: 11.6, h: 1.7, fontFace: font, fontSize: 28, bold: true, color: C.white, margin: 0, fit: "shrink"
  });
  ["患者さんはボタンで回答", "医療者は一覧で確認", "災害時も通常診療も活用"].forEach((t, i) => {
    pill(s, t, 1.2 + i * 3.65, 4.35, 2.75, i % 2 ? C.mint : C.mint2, i % 2 ? C.blue : C.green, 9);
  });
  s.addText("“電話が集中する前に、対応が必要な患者さんを見つける”", { x: 1.0, y: 5.65, w: 11.3, h: 0.42, fontFace: font, fontSize: 22, bold: true, color: "DFF4ED", align: "center", margin: 0 });
  s.addText("熊本中央病院 糖尿病・内分泌・代謝内科　西田 健朗", { x: 1.0, y: 6.72, w: 6.2, h: 0.2, fontFace: font, fontSize: 9.3, color: "EAF4F7", margin: 0 });
}

[slide1, slide2, slide3, slide4, slide5, slide6, slide7, slide8, slide9, slide10, slide11].forEach(fn => fn());

pptx.writeFile({ fileName: "/Users/Kenro/Documents/Codex/2026-04-25/chatgpt-line/MedSafetyLink/medsafety_link_jds_clinician_slides.pptx" });
