# Trust X

署名可能なプロフィール交換ネットワークサービス。

次のことを実現したい。

- トラストレスな署名付きのプロフィール
  - 他のネットワークに簡単にインポート可能
  - ヒューマンフレンドリーなテキストデータに変換可能
  - プロフィール情報を始めとした様々なデータへの署名機能
- 様々なモジュールを後から導入可能

プロフィールの YAML 例を次に示す。

```yaml
Base58_ContestProviderA_Sig_For_Skills:
  by: Base58_ContestProviderA_PublicKey
  to: Base58_User_PublicKey
  data:
    skills:
      word:
        level: 3
      excel:
        level: 3
    signed: 2019-01-01T03:00:00

Base58_ContestProviderB_Sig_For_Skills:
  by: Base58_ContestProviderB_PublicKey
  to: Base58_User_PublicKey
  data:
    skills:
      簿記:
        level: 3
    signed: 2019-02-01T12:00:00+09:00

Base58_ClientA_Sig_For_Experiences:
  by: Base58_ClientA_PublicKey
  to: Base58_User_PublicKey
  data:
    experiences:
      企業 A 経理事務:
        since: 2019-01-01T10:00:00+09:00
        until: 2019-12-28T19:00:00+09:00
        tags: [word, excel, 簿記]
        text: 神奈川県にある企業様の経理事務を担当しました。
    signed: 2019-12-28T19:00:00+09:00

Base58_FriendA_Sig_For_Experiences_And_Reputations:
  by: Base58_FriendA_PublicKey
  to: Base58_User_PublicKey
  data:
    experiences:
      - title: 知人 A 経理事務
        since: 2020-01-01T10:00:00+09:00
        until: 2020-01-31T19:00:00+09:00
        tags: [word, excel, 簿記]
        text: 知人の経理事務を支援しました。
    reputations:
      - いつも助けていただいています。ありがとう！
    signed: 2020-01-31T19:00:00+09:00

Base58_ClientB_Sig_For_Experiences_And_Reputations:
  by: Base58_ClientB_PublicKey
  to: Base58_User_PublicKey
  data:
    experiences:
      - title: 企業 B 経理事務
        since: 2020-01-01T10:00:00+09:00
        until: 2020-12-28T19:00:00+09:00
        tags: [word, excel, 簿記]
        text: 埼玉県にある企業様の経理事務を担当しました。
    reputations:
      - とても真面目な良い方です。
    signed: 2020-12-28T19:00:00+09:00

Base58_ClientA_Sig_For_Reputations:
  by: Base58_ClientA_PublicKey
  to: Base58_User_PublicKey
  data:
    reputations:
      - とても真面目な良い方です。
    signed: 2019-12-28T19:00:00+09:00
```

この人のスキルを証明するためのコンテスト主催者による署名例を次に示す。

コンテスト主催者の鍵を作成する。

```sh
python -m trustx gen --secret-key ./contest-provider.secret.key \
                     --public-key ./contest-provider.public.key
```

ユーザーの鍵を作成する。

```sh
python -m trustx gen --public-key ./user.public.key
```

コンテストの成績データを用意する。

```sh
cat << EOF > user.skills.yaml
skills:
  word:
    level: 3
  excel:
    level: 3
signed: `python -m trustx date --timezone +0900 --format "%Y-%m-%d %H:%M:%S%:z"`
EOF
```

成績データをシリアライズする。

```sh
cat ./user.skills.yaml | python -c "import datetime, json, sys, yaml; print(json.dumps(yaml.safe_load(sys.stdin), default=lambda x: x.isoformat() if isinstance(x, datetime.datetime) else x, separators=(',', ':'), sort_keys=True), end='')" > ./user.skills.ser.json
```

ユーザーの鍵とコンテストの成績データを結合したファイルを作成する。

```sh
python -m trustx concat ./user.public.key ./user.skills.ser.json > ./user.skills.data
```

署名する。

```sh
python -m trustx sign --secret-key ./contest-provider.secret.key ./user.skills.data > ./user.skills.data.sig
python -m trustx base58 ./user.skills.data.sig
```

```
2HaK4mYEPt65GCYfMVyF6GE4jc9DJJ1BHhVUg57mv4wY6PnLXabjHKM2kj4uLJdGq31De1BKmV9VQMG4sncngAj
```

署名を検証する。

```sh
python -m trustx verify --public-key ./contest-provider.public.key \
                        --data ./user.skills.data \
                        ./user.skills.data.sig
```

```
OK
```

コンテスト主催者の公開鍵 (Base58) を取得する。

```sh
python -m trustx base58 ./contest-provider.public.key
```

```
uJkHWNFwPVci3LEpzHLfq6efiSpRwJSAQUZsqTLR82Ro
```

ユーザーの公開鍵 (Base58) を取得する。

```sh
python -m trustx base58 ./user.public.key
```

```
iAQcYdrGxQei8yjwsW86p8eV2AntsPwriWY8pYonz9Sx
```

署名をキーにし、コンテスト主催者のアドレスとデータを含めた YAML を作成する。

```sh
cat user.blocks.yaml
```

```yaml
2HaK4mYEPt65GCYfMVyF6GE4jc9DJJ1BHhVUg57mv4wY6PnLXabjHKM2kj4uLJdGq31De1BKmV9VQMG4sncngAj:
  by: uJkHWNFwPVci3LEpzHLfq6efiSpRwJSAQUZsqTLR82Ro
  to: iAQcYdrGxQei8yjwsW86p8eV2AntsPwriWY8pYonz9Sx
  data:
    skills:
      word:
        level: 3
      excel:
        level: 3
    signed: 2020-07-03 13:52:42+09:00
```

一連の処理は、次のコマンドで代用できる。

```sh
# Sign
python -m trustx.profiles sign --by ./contest-provider.secret.key \
                               --to ./user.public.key \
                               ./user.skills.yaml >> ./user.blocks.yaml

# Verify
python -m trustx.profiles verify ./user.blocks.yaml
```

```
OK
```

このような非常にシンプルな証明と検証のプロトコルを用いる。

特徴は次の通り。

- Bitcoin ブロックチェーンとの共通点
    - 楕円曲線電子署名アルゴリズム (ECDSA)
    - バイナリデータのウェブセーフな表現に Base58 を使用
    - 公開鍵のアドレス変換処理
- 秘密鍵の漏洩や紛失は信用の損失に直結する
    - コンテストプロバイダを始めとした組織では HSM の導入を推奨
    - 署名日時をデータに含めたところで対策にはならない
    - 署名履歴から新しい鍵で署名し直すのが主なリカバリ案となる


## ストレージモジュール

- trustx パッケージ共通のストレージ

```python
import trustx.storages
```


## プロフィールモジュール

- プロフィールを操作する

```python
from trustx.profiles import Profiles
from trustx.storages import LocalStorage

profiles = Profiles(LocalStorage())
print('number of profiles is', len(profiles))
```


## セッションモジュール

サービスへのサインアップおよびサインインに用いる。

```python
from datetime import timedelta
from trustx.sessions import HMACSessionFactory

payload = b'payload1', b'payload2'

Session = HMACSessionFactory(b'your_secret')
session1 = Session(*payload, life=timedelta(hours=1))
assert session1, 'invalid session'

session2 = Session.parse(session1.token)
assert session2 == session1
assert session2.data == payload
```


## コンペティションモジュール

内容は次の通り。

- いずれのユーザーも必要条件を満たせば開催および参加が可能
- 必要条件は任意に決められる (課金が必要, etc.)
- コンペティションは、他ユーザーのタイムラインのような位置に掲載される
- 具体的な開催の流れ
    1. ユーザー A が、コンペティションを作成し、参加者を募集
    2. コンペティションにユーザー B, C, D が応募
    3. ユーザー A が、コンペティションの募集を締め切る
    4. ユーザー A が、ユーザー B, C に返信

```python
from trustx.competitions import Competitions
from trustx.storages import LocalStorage

competitions = Competitions(LocalStorage())

for competition in competitions:
    if competition.active:
        print(competition, 'is active')
```


### 依存モジュール

- セッションモジュール


## 業務委託契約サポートモジュール

あくまでサポートであってデータの永続化を含め一切の責任を負わない。

```python
from trustx.contracts import Contracts
from trustx.storages import LocalStorage

contracts = Contracts(LocalStorage())

for contract in contracts:
    print('support for', contract.contractor, 'and', contract.contractee)
```


### 依存モジュール

- コンペティションモジュール


### 準委任契約清算関数

業務委託契約の一つである準委任契約は複雑な時間契約になっていることが多いため、計算の一例を次に示す。

清算方法は、主に次の種類がある。

1. 無課金帯の有無にかかわらず、同額の時給で算出する方法
2. 原点より無課金帯始点と無課金帯終点に接する二種類の直線で算出する方法

両者を実現する汎用的な関数の例は次の通り。

```python
timeandmaterials = [(140, 2000),
                    (180, 0),
                    (float('inf'), 1500)]

def f(hours):
    r = 0
    prev = 0
    for h, price in timeandmaterials:
        diff = h - prev
        r += min(hours, diff) * price
        hours -= diff
        if hours <= 0:
            break
        prev = h
    return r

print(f(181))
```


## 課金モジュール

課金モジュールを導入することで、決済機能を追加し、サービスの挙動を変えることができる。

有効期間を持つサービスの提供、いわゆるサブスクライブによるコンペティションの挙動の変化の例を次に示す。

プラン|料金 (円)|有効期間|サービス内容|備考
--|--|--|--|--
Free|0|一ヶ月|応募可能数 5 回|期間を過ぎたらリセット
Pro|3,000|一ヶ月|応募可能数 * 回|期間を過ぎたらリセット

対して、有効期間のないサービスを提供する場合の例を次に示す。

サービス名|料金 (円)|サービス内容|備考
--|--|--|--
コンペティション開催|10,000|一ヶ月間、開催情報が掲載される|実行時に課金が発生
何らかのポイント追加|3,000|+100pt|実行時に課金が発生

```python
from trustx.payments import Payments
from trustx.storages import LocalStorage

payments = Payments(LocalStorage())
print('number of payments is', len(payments))
```


## サーバーモジュール

- 主に Web API を提供

```sh
TRUSTX_SESSION_SECRET=your_secret python -m trustx.servers wsgi
```

もしくは

```python
from wsgiref.simple_server import make_server
from trustx.servers import wsgi
from trustx.sessions import HMACSessionFactory
from trustx.storages import LocalStorage

wsgi.storage = LocalStorage()
wsgi.session = HMACSessionFactory(b'your_secret')

with make_server('', 8000, wsgi) as httpd:
    print('Serving HTTP on port 8000, control-C to stop')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Shutting down.')
```


## 標準 Web UI

- 標準のサーバーモジュール Web API 用 UI

```sh
cd ui
python -m http.server
```
