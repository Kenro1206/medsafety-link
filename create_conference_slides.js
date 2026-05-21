const pptxgen = require("pptxgenjs");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "MedSafety Link";
pptx.subject = "MedSafety Link conference presentation";
pptx.title = "LINEを活用した糖尿病患者安否・症状確認システム MedSafety Link";
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
  blue: "185E98",
  blue2: "2F6FE4",
  teal: "257E6F",
  mint: "EAF4F7",
  mint2: "DFF4ED",
  green: "166F77",
  red: "C9342D",
  orange: "E18B2D",
  gray: "64748B",
  light: "F7FAFC",
  white: "FFFFFF",
  line: "DCE6EF",
  darkLine: "B9C7D4",
};

const font = "Yu Gothic";

function addBg(slide, color = C.light) {
  slide.background = { color };
}

function addHeader(slide, section, n) {
  slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 0.25, fill: { color: C.blue }, line: { color: C.blue } });
  slide.addText(section, { x: 0.45, y: 0.34, w: 9.6, h: 0.25, fontFace: font, fontSize: 8.5, color: C.gray, bold: true });
  slide.addText(String(n).padStart(2, "0"), { x: 12.2, y: 0.29, w: 0.6, h: 0.28, fontFace: font, fontSize: 9, color: C.gray, align: "right" });
}

function title(slide, text, sub) {
  slide.addText(text, { x: 0.6, y: 0.68, w: 11.7, h: 0.55, fontFace: font, fontSize: 25, bold: true, color: C.navy, margin: 0 });
  if (sub) slide.addText(sub, { x: 0.62, y: 1.26, w: 10.8, h: 0.3, fontFace: font, fontSize: 9.5, color: C.gray, margin: 0 });
}

function pill(slide, text, x, y, w, color = C.mint, textColor = C.green) {
  slide.addShape(pptx.ShapeType.roundRect, { x, y, w, h: 0.34, rectRadius: 0.08, fill: { color }, line: { color } });
  slide.addText(text, { x: x + 0.08, y: y + 0.075, w: w - 0.16, h: 0.15, fontFace: font, fontSize: 8, bold: true, color: textColor, align: "center", margin: 0 });
}

function card(slide, x, y, w, h, opts = {}) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h,
    rectRadius: 0.08,
    fill: { color: opts.fill || C.white },
    line: { color: opts.line || C.line, width: 1 },
    shadow: opts.shadow ? { type: "outer", color: "AAB4BF", opacity: 0.12, blur: 1, angle: 45, distance: 1 } : undefined,
  });
}

function bulletList(slide, items, x, y, w, fs = 11, color = C.navy) {
  slide.addText(items.map(t => ({ text: t, options: { bullet: { type: "ul" }, breakLine: true } })), {
    x, y, w, h: 1.8, fontFace: font, fontSize: fs, color, breakLine: false,
    fit: "shrink", margin: 0.04, paraSpaceAfterPt: 5,
  });
}

function metric(slide, label, value, x, y, color = C.blue) {
  card(slide, x, y, 2.25, 0.95, { fill: C.white, shadow: true });
  slide.addText(label, { x: x + 0.14, y: y + 0.13, w: 1.95, h: 0.18, fontFace: font, fontSize: 7.6, color: C.gray, bold: true, margin: 0 });
  slide.addText(value, { x: x + 0.14, y: y + 0.35, w: 1.95, h: 0.42, fontFace: font, fontSize: 24, color, bold: true, margin: 0 });
}

function arrow(slide, x1, y1, x2, y2, color = C.blue) {
  slide.addShape(pptx.ShapeType.line, { x: x1, y: y1, w: x2 - x1, h: y2 - y1, line: { color, width: 2, beginArrowType: "none", endArrowType: "triangle" } });
}

function phoneMock(slide, x, y, w, h) {
  slide.addShape(pptx.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.18, fill: { color: "111827" }, line: { color: "111827" } });
  slide.addShape(pptx.ShapeType.roundRect, { x: x + 0.12, y: y + 0.12, w: w - 0.24, h: h - 0.24, rectRadius: 0.12, fill: { color: "EEF7F4" }, line: { color: "EEF7F4" } });
  slide.addText("患者さんのLINE画面", { x: x + 0.25, y: y + 0.35, w: w - 0.5, h: 0.25, fontFace: font, fontSize: 8.4, bold: true, color: C.green, margin: 0 });
  card(slide, x + 0.32, y + 0.78, w - 0.64, 1.35, { fill: C.white });
  slide.addText("【安否確認】現在の状況を返信してください。", { x: x + 0.47, y: y + 0.92, w: w - 0.94, h: 0.28, fontFace: font, fontSize: 7.5, color: C.navy, margin: 0 });
  const qs = ["無事", "体調不良", "薬不足", "至急連絡"];
  qs.forEach((q, i) => pill(slide, q, x + 0.47 + (i % 2) * 1.38, y + 1.28 + Math.floor(i / 2) * 0.36, 1.18, C.mint2, C.green));
  card(slide, x + 0.32, y + 2.35, w - 0.64, 0.58, { fill: C.white });
  slide.addText("写真・位置情報も送信可能", { x: x + 0.47, y: y + 2.54, w: w - 0.94, h: 0.18, fontFace: font, fontSize: 7.4, color: C.navy, margin: 0 });
}

function dashboardMock(slide, x, y, w, h) {
  card(slide, x, y, w, h, { fill: C.white, shadow: true });
  slide.addText("ダッシュボード", { x: x + 0.25, y: y + 0.18, w: w - 0.5, h: 0.25, fontFace: font, fontSize: 11, color: C.blue, bold: true, margin: 0 });
  metric(slide, "患者数", "120", x + 0.28, y + 0.63, C.navy);
  metric(slide, "回答済", "86", x + 2.72, y + 0.63, C.green);
  metric(slide, "未回答", "34", x + 0.28, y + 1.75, C.orange);
  metric(slide, "緊急未対応", "3", x + 2.72, y + 1.75, C.red);
  slide.addShape(pptx.ShapeType.roundRect, { x: x + 0.28, y: y + 3.02, w: w - 0.56, h: 0.58, rectRadius: 0.06, fill: { color: "FFF4F2" }, line: { color: "F1BBB8" } });
  slide.addText("重症アラート: 至急確認が必要な回答を優先表示", { x: x + 0.45, y: y + 3.2, w: w - 0.9, h: 0.18, fontFace: font, fontSize: 7.5, bold: true, color: C.red, margin: 0 });
}

function addSlide1() {
  const s = pptx.addSlide(); addBg(s, C.blue);
  s.addShape(pptx.ShapeType.rect, { x: 8.4, y: 0, w: 4.94, h: 7.5, fill: { color: C.teal, transparency: 10 }, line: { color: C.teal, transparency: 100 } });
  s.addText("MedSafety Link", { x: 0.62, y: 0.55, w: 4.2, h: 0.35, fontFace: font, fontSize: 14, bold: true, color: C.white, margin: 0 });
  s.addText("LINEを活用した糖尿病患者\\n安否・症状確認システムの開発", { x: 0.62, y: 1.55, w: 8.2, h: 1.3, fontFace: font, fontSize: 31, bold: true, color: C.white, margin: 0, breakLine: false, fit: "shrink" });
  s.addText("災害時・通常診療を支える患者連絡支援基盤", { x: 0.66, y: 3.02, w: 7.5, h: 0.32, fontFace: font, fontSize: 14, color: "DDEBFF", bold: true, margin: 0 });
  phoneMock(s, 9.1, 1.12, 2.7, 4.0);
  dashboardMock(s, 6.35, 4.68, 5.7, 2.2);
  s.addText("日本糖尿病インフォマティクス学会", { x: 0.66, y: 6.45, w: 5.4, h: 0.24, fontFace: font, fontSize: 10, color: C.white, bold: true, margin: 0 });
  s.addText("熊本中央病院 糖尿病・内分泌・代謝内科　西田 健朗", { x: 0.66, y: 6.78, w: 6.6, h: 0.24, fontFace: font, fontSize: 9, color: "EAF4F7", margin: 0 });
}

function addSlide2() {
  const s = pptx.addSlide(); addBg(s); addHeader(s, "背景", 2);
  title(s, "電話が集中する状況で、誰に対応すべきかを早く知る", "災害時も通常診療の補助も、患者連絡は“量”と“優先順位”が課題になる");
  const items = [
    ["災害時", "安否・所在・薬剤不足を短時間で把握したい"],
    ["通常時", "体調変化、足病変写真、通院困難の連絡を拾いたい"],
    ["医療者側", "電話・個別LINE・紙管理では履歴と優先順位が散らばる"],
  ];
  items.forEach((it, i) => {
    const x = 0.75 + i * 4.1;
    card(s, x, 2.05, 3.5, 3.25, { fill: C.white, shadow: true });
    s.addText(it[0], { x: x + 0.25, y: 2.32, w: 2.9, h: 0.3, fontFace: font, fontSize: 17, bold: true, color: [C.blue, C.teal, C.red][i], margin: 0 });
    s.addText(it[1], { x: x + 0.25, y: 3.05, w: 2.95, h: 1.45, fontFace: font, fontSize: 14, bold: true, color: C.navy, fit: "shrink", margin: 0 });
  });
  s.addText("必要なのは、連絡手段ではなく「要対応患者を見つける仕組み」", { x: 1.0, y: 6.18, w: 11.3, h: 0.38, fontFace: font, fontSize: 20, bold: true, color: C.green, align: "center", margin: 0 });
}

function addSlide3() {
  const s = pptx.addSlide(); addBg(s); addHeader(s, "コンセプト", 3);
  title(s, "LINEを入口に、回答・写真・位置情報を管理画面へ集約", "患者にとっては簡単、医療者にとっては一覧化・優先順位化しやすい設計");
  phoneMock(s, 0.8, 1.75, 2.85, 4.25);
  arrow(s, 3.9, 3.7, 5.05, 3.7, C.blue);
  dashboardMock(s, 5.3, 1.9, 5.3, 3.8);
  arrow(s, 10.75, 3.7, 11.72, 3.7, C.teal);
  card(s, 11.85, 2.25, 1.1, 2.9, { fill: C.mint2 });
  s.addText("対応", { x: 12.02, y: 3.2, w: 0.8, h: 0.35, fontFace: font, fontSize: 18, bold: true, color: C.green, align: "center", margin: 0 });
  ["ボタン回答", "写真", "位置情報", "履歴保存"].forEach((t, i) => pill(s, t, 1.05 + i * 2.25, 6.45, 1.7, i % 2 ? C.mint : C.mint2, i % 2 ? C.blue : C.green));
}

function addSlide4() {
  const s = pptx.addSlide(); addBg(s); addHeader(s, "システム構成", 4);
  title(s, "Render上のWebアプリを中心に、LINEとGoogle Workspaceを連携", "施設IDごとにLINE・Google Sheets・Driveを分離して運用できる");
  const nodes = [
    ["患者LINE", 0.7, 2.0, C.green],
    ["LINE Messaging API", 3.1, 2.0, C.blue],
    ["MedSafety Link\\n(Render)", 5.65, 1.85, C.navy],
    ["Google Sheets\\n患者・回答・履歴", 8.55, 1.35, C.teal],
    ["Google Drive\\n写真保存", 8.55, 3.05, C.orange],
    ["Looker Studio\\n可視化", 10.9, 2.2, C.red],
  ];
  nodes.forEach(([txt, x, y, color]) => {
    card(s, x, y, 1.95, 0.95, { fill: C.white, shadow: true });
    s.addText(txt, { x: x + 0.12, y: y + 0.22, w: 1.7, h: 0.38, fontFace: font, fontSize: 10.5, bold: true, color, align: "center", margin: 0, fit: "shrink" });
  });
  arrow(s, 2.68, 2.48, 3.1, 2.48); arrow(s, 5.05, 2.48, 5.65, 2.48); arrow(s, 7.65, 2.35, 8.55, 1.82, C.teal); arrow(s, 7.65, 2.72, 8.55, 3.48, C.orange); arrow(s, 10.5, 1.82, 10.9, 2.48, C.red);
  card(s, 1.25, 5.45, 10.9, 0.82, { fill: C.mint });
  s.addText("施設ごとの設定: 施設ID / パスワード / LINEチャネル / Googleスプレッドシート / Driveフォルダ", { x: 1.5, y: 5.72, w: 10.4, h: 0.2, fontFace: font, fontSize: 11, bold: true, color: C.navy, align: "center", margin: 0 });
}

function addSlide5() {
  const s = pptx.addSlide(); addBg(s); addHeader(s, "機能", 5);
  title(s, "医療者側の画面は“対応が必要な人から見る”ために設計", "一斉送信、未回答再送、回答履歴、個別送信を一つの管理画面に集約");
  dashboardMock(s, 0.75, 1.72, 5.6, 4.25);
  const features = [
    ["一斉送信", "対象者を検索・選択して回答ボタン付きLINEを送信"],
    ["重症アラート", "低血糖・薬剤不足・至急連絡希望などを優先表示"],
    ["回答履歴", "時刻、回答内容、対応状況、送信履歴を保存"],
    ["写真・位置情報", "足病変写真や現在地をリンクで確認"],
  ];
  features.forEach((f, i) => {
    const y = 1.75 + i * 1.05;
    card(s, 7.0, y, 5.6, 0.8, { fill: i % 2 ? C.white : C.mint });
    s.addText(f[0], { x: 7.25, y: y + 0.18, w: 1.6, h: 0.22, fontFace: font, fontSize: 12, bold: true, color: C.blue, margin: 0 });
    s.addText(f[1], { x: 8.78, y: y + 0.16, w: 3.5, h: 0.26, fontFace: font, fontSize: 9.5, color: C.navy, margin: 0, fit: "shrink" });
  });
}

function addSlide6() {
  const s = pptx.addSlide(); addBg(s); addHeader(s, "患者体験", 6);
  title(s, "患者さんはアプリを覚えず、普段のLINEで回答できる", "ボタン回答を中心に、必要時のみ自由記述・写真・位置情報を送信");
  phoneMock(s, 1.0, 1.55, 3.05, 4.55);
  const flow = [
    ["1", "通知を受信"],
    ["2", "ボタンで回答"],
    ["3", "必要時に写真・位置情報"],
    ["4", "医療者が確認"],
  ];
  flow.forEach((f, i) => {
    const x = 4.7 + i * 2.0;
    s.addShape(pptx.ShapeType.ellipse, { x, y: 2.42, w: 0.58, h: 0.58, fill: { color: C.blue }, line: { color: C.blue } });
    s.addText(f[0], { x, y: 2.58, w: 0.58, h: 0.16, fontFace: font, fontSize: 10, bold: true, color: C.white, align: "center", margin: 0 });
    s.addText(f[1], { x: x - 0.35, y: 3.28, w: 1.25, h: 0.45, fontFace: font, fontSize: 11.5, bold: true, color: C.navy, align: "center", margin: 0, fit: "shrink" });
    if (i < flow.length - 1) arrow(s, x + 0.7, 2.72, x + 1.52, 2.72, C.teal);
  });
  card(s, 4.75, 4.72, 7.35, 0.8, { fill: C.mint2 });
  s.addText("緊急時はLINEではなく電話・救急外来受診を促す文言を明示", { x: 5.0, y: 4.98, w: 6.85, h: 0.22, fontFace: font, fontSize: 11.2, bold: true, color: C.green, align: "center", margin: 0 });
}

function addSlide7() {
  const s = pptx.addSlide(); addBg(s); addHeader(s, "対象領域", 7);
  title(s, "同じ基盤を、1型糖尿病・透析・足病変で使い分ける", "施設・部門ごとに文面、回答ボタン、Google連携を設定可能");
  const rows = [
    ["1型糖尿病", "低血糖、薬・インスリン不足、至急連絡希望を重視", C.blue],
    ["透析患者", "透析可否、シャント不安、体調不良を確認", C.teal],
    ["足病変", "写真、発赤・痛み、浸出液、悪化徴候を確認", C.orange],
  ];
  rows.forEach((r, i) => {
    const y = 1.75 + i * 1.35;
    card(s, 1.0, y, 11.2, 1.0, { fill: C.white, shadow: true });
    s.addShape(pptx.ShapeType.roundRect, { x: 1.25, y: y + 0.19, w: 1.65, h: 0.58, rectRadius: 0.1, fill: { color: r[2] }, line: { color: r[2] } });
    s.addText(r[0], { x: 1.37, y: y + 0.37, w: 1.42, h: 0.16, fontFace: font, fontSize: 9, bold: true, color: C.white, align: "center", margin: 0 });
    s.addText(r[1], { x: 3.25, y: y + 0.28, w: 8.35, h: 0.28, fontFace: font, fontSize: 14, bold: true, color: C.navy, margin: 0 });
  });
  s.addText("共通基盤 + 領域別プリセット = 横展開しやすい運用", { x: 1.0, y: 6.05, w: 11.2, h: 0.34, fontFace: font, fontSize: 20, bold: true, color: C.green, align: "center", margin: 0 });
}

function addSlide8() {
  const s = pptx.addSlide(); addBg(s); addHeader(s, "データ活用", 8);
  title(s, "回答データは記録され、地図・重症度・地域別集計へ展開可能", "Google Sheetsをデータ基盤としてLooker Studioに接続");
  card(s, 0.8, 1.75, 3.4, 3.55, { fill: C.white, shadow: true });
  s.addText("responses", { x: 1.1, y: 2.02, w: 2.8, h: 0.25, fontFace: font, fontSize: 14, bold: true, color: C.blue, align: "center", margin: 0 });
  ["timestamp", "patient_id", "code / label", "severity", "latitude / longitude"].forEach((t, i) => {
    pill(s, t, 1.25, 2.55 + i * 0.48, 2.5, i % 2 ? C.mint : C.mint2, i % 2 ? C.blue : C.green);
  });
  arrow(s, 4.4, 3.52, 5.25, 3.52, C.teal);
  card(s, 5.4, 1.75, 6.95, 3.55, { fill: C.white, shadow: true });
  s.addText("Looker Studio可視化イメージ", { x: 5.7, y: 2.02, w: 6.35, h: 0.25, fontFace: font, fontSize: 14, bold: true, color: C.blue, align: "center", margin: 0 });
  metric(s, "未対応", "34", 5.9, 2.55, C.orange);
  metric(s, "重症", "3", 8.35, 2.55, C.red);
  s.addShape(pptx.ShapeType.rect, { x: 5.92, y: 3.78, w: 5.8, h: 0.75, fill: { color: C.mint }, line: { color: C.mint } });
  s.addText("都道府県・患者区分・重症度で絞り込み", { x: 6.15, y: 4.02, w: 5.3, h: 0.2, fontFace: font, fontSize: 11, bold: true, color: C.green, align: "center", margin: 0 });
  s.addText("地図表示: 位置情報を送信した患者の所在地確認", { x: 5.95, y: 4.75, w: 5.7, h: 0.2, fontFace: font, fontSize: 9.5, color: C.gray, align: "center", margin: 0 });
}

function addSlide9() {
  const s = pptx.addSlide(); addBg(s); addHeader(s, "実装・運用", 9);
  title(s, "多施設運用を前提に、設定を画面から完結できるよう設計", "非エンジニアでも導入できることを重視");
  const blocks = [
    ["施設ID管理", "施設ごとにログイン、LINE、Google Sheetsを分離"],
    ["Google連携手順", "サービスアカウント、共有先メール、初期化を画面で案内"],
    ["LINE接続診断", "Webhook受信、destination、アクセストークンを確認"],
    ["運用マニュアル", "患者登録、送信、トラブル対応をサイト内に掲載"],
  ];
  blocks.forEach((b, i) => {
    const x = 0.85 + (i % 2) * 6.0;
    const y = 1.8 + Math.floor(i / 2) * 1.65;
    card(s, x, y, 5.45, 1.25, { fill: i % 2 ? C.white : C.mint, shadow: true });
    s.addText(b[0], { x: x + 0.25, y: y + 0.22, w: 2.1, h: 0.25, fontFace: font, fontSize: 13, bold: true, color: C.blue, margin: 0 });
    s.addText(b[1], { x: x + 0.25, y: y + 0.62, w: 4.95, h: 0.3, fontFace: font, fontSize: 10.2, color: C.navy, margin: 0, fit: "shrink" });
  });
  s.addText("院内スタッフで動作確認し、実運用に向けて患者登録・LINE連携・写真/位置情報受信を整備", { x: 1.0, y: 5.75, w: 11.2, h: 0.35, fontFace: font, fontSize: 15.5, bold: true, color: C.green, align: "center", margin: 0 });
}

function addSlide10() {
  const s = pptx.addSlide(); addBg(s); addHeader(s, "期待される効果", 10);
  title(s, "電話連絡の負担を減らし、要対応患者への集中を支援", "災害時だけでなく、通常診療のフォローにも応用可能");
  const outcomes = [
    ["早い把握", "全体状況、未回答、重症アラートを短時間で確認"],
    ["対応の優先順位", "要対応者を一覧上で目立たせ、見落としを減らす"],
    ["記録性", "回答履歴・送信履歴を残し、後から確認できる"],
    ["拡張性", "1型糖尿病、透析、足病変などへ横展開できる"],
  ];
  outcomes.forEach((o, i) => {
    const x = 0.8 + i * 3.05;
    card(s, x, 2.0, 2.65, 3.25, { fill: C.white, shadow: true });
    s.addShape(pptx.ShapeType.ellipse, { x: x + 0.86, y: 2.28, w: 0.92, h: 0.92, fill: { color: [C.blue, C.teal, C.orange, C.red][i] }, line: { color: [C.blue, C.teal, C.orange, C.red][i] } });
    s.addText(String(i + 1), { x: x + 0.86, y: 2.54, w: 0.92, h: 0.18, fontFace: font, fontSize: 13, color: C.white, bold: true, align: "center", margin: 0 });
    s.addText(o[0], { x: x + 0.25, y: 3.55, w: 2.15, h: 0.28, fontFace: font, fontSize: 13, bold: true, color: C.navy, align: "center", margin: 0 });
    s.addText(o[1], { x: x + 0.25, y: 4.08, w: 2.15, h: 0.55, fontFace: font, fontSize: 9.5, color: C.gray, align: "center", margin: 0, fit: "shrink" });
  });
}

function addSlide11() {
  const s = pptx.addSlide(); addBg(s); addHeader(s, "今後の評価", 11);
  title(s, "今後は運用データに基づき、有用性と安全性を評価する", "導入可能性だけでなく、返信率・対応時間・運用負担を検証");
  const left = ["返信率・未回答率", "一斉送信から初回回答までの時間", "重症アラート確認までの時間", "電話連絡件数の変化", "スタッフの操作負担・受容性"];
  bulletList(s, left, 0.95, 2.0, 5.4, 12.5);
  card(s, 7.0, 1.75, 4.9, 3.9, { fill: C.mint, shadow: true });
  s.addText("評価デザイン案", { x: 7.35, y: 2.05, w: 4.2, h: 0.28, fontFace: font, fontSize: 15, bold: true, color: C.blue, align: "center", margin: 0 });
  const steps = ["院内デモ", "小規模患者群", "災害訓練", "多施設展開"];
  steps.forEach((st, i) => {
    s.addShape(pptx.ShapeType.roundRect, { x: 7.55, y: 2.72 + i * 0.62, w: 3.8, h: 0.38, rectRadius: 0.08, fill: { color: C.white }, line: { color: C.line } });
    s.addText(st, { x: 7.75, y: 2.82 + i * 0.62, w: 3.4, h: 0.12, fontFace: font, fontSize: 9.5, bold: true, color: C.navy, align: "center", margin: 0 });
  });
  s.addText("個人情報保護、緊急時は電話・救急外来という明確な案内を前提に運用", { x: 1.0, y: 6.1, w: 11.2, h: 0.26, fontFace: font, fontSize: 12.5, bold: true, color: C.red, align: "center", margin: 0 });
}

function addSlide12() {
  const s = pptx.addSlide(); addBg(s, C.navy);
  s.addText("結論", { x: 0.75, y: 0.75, w: 1.6, h: 0.35, fontFace: font, fontSize: 18, color: C.white, bold: true, margin: 0 });
  s.addText("MedSafety Linkは、LINEを入口に患者の安否・症状・写真・位置情報を集約し、医療者が要対応患者を優先把握するための患者連絡支援基盤である。", {
    x: 0.9, y: 1.75, w: 11.6, h: 1.35, fontFace: font, fontSize: 27, bold: true, color: C.white, margin: 0, fit: "shrink"
  });
  const conclusions = [
    "災害時の安否確認",
    "通常診療での症状把握",
    "多施設・多領域への横展開",
  ];
  conclusions.forEach((t, i) => pill(s, t, 1.0 + i * 3.7, 4.0, 2.8, i === 0 ? C.mint2 : C.mint, i === 0 ? C.green : C.blue));
  s.addText("“連絡が来た人を探す” から “対応が必要な人から見る” へ", {
    x: 1.0, y: 5.45, w: 11.3, h: 0.45, fontFace: font, fontSize: 22, bold: true, color: "DFF4ED", align: "center", margin: 0
  });
  s.addText("熊本中央病院 糖尿病・内分泌・代謝内科　西田 健朗", { x: 1.0, y: 6.65, w: 6.3, h: 0.2, fontFace: font, fontSize: 9.5, color: "EAF4F7", margin: 0 });
}

[addSlide1, addSlide2, addSlide3, addSlide4, addSlide5, addSlide6, addSlide7, addSlide8, addSlide9, addSlide10, addSlide11, addSlide12].forEach(fn => fn());

pptx.writeFile({ fileName: "/Users/Kenro/Documents/Codex/2026-04-25/chatgpt-line/MedSafetyLink/medsafety_link_conference_slides.pptx" });
