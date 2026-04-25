# MedSafety Link 実働手順

## 1. 施設を作成する
管理画面の「施設ID管理」で施設ID、施設名、初期パスワードを登録します。
ログイン画面では、その施設IDとパスワードを使います。

## 2. LINEを設定する
各施設の「設定」で、LINE Developers の Messaging API チャネルアクセストークンを保存します。
Webhook URL は公開URLに `/callback` を付けたものを LINE Developers に設定します。

例: `https://example.com/callback`

## 3. Google Sheetsを設定する
GoogleサービスアカウントJSONをアップロードし、スプレッドシートIDを保存します。
スプレッドシートはサービスアカウントの `client_email` に編集権限で共有してください。

保存後、セットアップ画面の「Googleシート初期化」を押すと、以下のタブを作成/確認します。

- `patients`
- `pending_users`
- `responses`
- `system_mode`

## 4. 疎通確認
セットアップ画面で以下を順に確認します。

- LINE接続テスト
- Google接続テスト
- Googleシート初期化

## 5. Renderで公開

このリポジトリには `render.yaml` を含めています。Render Dashboard で GitHub リポジトリを接続し、Blueprint として作成すると以下で起動します。

- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 --max-requests 200 --max-requests-jitter 50`
- Health Check Path: `/healthz`
- Settings保存先: `/var/data/settings.json`

Render の公開URLが `https://medsafety-link.onrender.com` の場合、LINE Developers の Webhook URL は次です。

```text
https://medsafety-link.onrender.com/callback
```

`GOOGLE_SERVICE_JSON` は Render の Environment で Secret として設定できます。画面からJSONをアップロードして使う場合は、永続ディスクに保存される `settings.json` と組み合わせて運用します。

## 6. 本番起動
ローカル確認:

```bash
python3 -m flask --app app run --host 127.0.0.1 --port 5001
```

本番プロセス:

```bash
gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 --max-requests 200 --max-requests-jitter 50
```

ヘルスチェック:

```text
/healthz
```

## 7. 実働前チェック

- `FLASK_SECRET_KEY` をランダムな長い文字列に変更済み
- `service_account.json` はGit管理外
- 各施設のLINEトークンを設定済み
- 各施設のスプレッドシートIDを設定済み
- 管理者LINE IDを設定済み
- LINE Developers の Webhook URL が公開URL + `/callback`
- LINE Developers の Webhook利用がON
