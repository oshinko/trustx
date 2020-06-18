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
BASE58_ContestProviderA_Sig_For_Skills:
  by: BASE58_ContestProviderA_Address
  data:
    skills:
      word:
        level: 3
      excel:
        level: 3
    signed: 2019-01-01T03:00:00

BASE58_ContestProviderB_Sig_For_Skills:
  by: BASE58_ContestProviderB_Address
  data:
    skills:
      簿記:
        level: 3
    signed: 2019-02-01T12:00:00+09:00

BASE58_ClientA_Sig_For_Experiences:
  by: BASE58_ClientA_Address
  data:
    experiences:
      企業 A 経理事務:
        since: 2019-01-01T10:00:00+09:00
        until: 2019-12-28T19:00:00+09:00
        tags: [word, excel, 簿記]
        text: 神奈川県にある企業様の経理事務を担当しました。
    signed: 2019-12-28T19:00:00+09:00

BASE58_FriendA_Sig_For_Experiences_And_Reputations:
  by: BASE58_FriendA_Address
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

BASE58_ClientB_Sig_For_Experiences_And_Reputations:
  by: BASE58_ClientB_Address
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

BASE58_ClientA_Sig_For_Reputations:
  by: BASE58_ClientA_Address
  data:
    reputations:
      - とても真面目な良い方です。
    signed: 2019-12-28T19:00:00+09:00
```

この人のスキルを証明するためのコンテスト主催者による署名例を次に示す。

コンテスト主催者のキーを作成する。

```sh
python -m trustx gen --signing-key ./contest-provider.signing.key \
                     --verifying-key ./contest-provider.verifying.key
```

ユーザーのキーを取得する。
本来、ユーザー自信がキーペアを作成するが、例として検証キーのみ作成する。

```sh
python -m trustx gen --verifying-key ./user.verifying.key
```

コンテストの成績データを用意する。
この時点で署名日時を含める。

```sh
cat << EOF > user.skills.yaml
skills:
  word:
    level: 3
  excel:
    level: 3
signed: `date +%Y-%m-%dT%H:%M:%S%:z`
EOF
```

ユーザーのキーとコンテストの成績データを結合したファイルを作成する。

```sh
python -m trustx concat ./user.verifying.key ./user.skills.yaml > ./user.skills.data
```

署名する。

```sh
python -m trustx sign --signing-key ./contest-provider.signing.key ./user.skills.data > ./user.skills.data.sig
python -m trustx base58 ./user.skills.data.sig
```

```
4bjnskhE4MF3Mn59QzDfvuJTRCyNMU8n9e1PZiExXDEVE5XiW1LVTcD3MEseu5ze9udk3LabV6RvpFNgTuhbthKk
```

署名を検証する。

```sh
python -m trustx verify --verifying-key ./contest-provider.verifying.key \
                      --data ./user.skills.data \
                      ./user.skills.data.sig
```

```
OK
```

コンテスト主催者のアドレスを取得する。

```sh
python -m trustx addr --signing-key ./contest-provider.signing.key
```

```
1LtfiUjeeZL3q4CneVAFd3M8a3wi3Sy8x9
```

ユーザーのアドレスを取得する。

```sh
python -m trustx addr --verifying-key ./user.verifying.key
```

```
1NgQCSskEmtRg7xeFJnWRzt875czviaLwF
```

署名をキーにし、コンテスト主催者のアドレスとデータを含めた YAML を作成する。

ユーザーのアドレスを示す `to` は、システムの文脈から自明ならば省略できる。

```yaml
4bjnskhE4MF3Mn59QzDfvuJTRCyNMU8n9e1PZiExXDEVE5XiW1LVTcD3MEseu5ze9udk3LabV6RvpFNgTuhbthKk:
  by: 1LtfiUjeeZL3q4CneVAFd3M8a3wi3Sy8x9
  to: 1NgQCSskEmtRg7xeFJnWRzt875czviaLwF
  data:
    skills:
      word:
        level: 3
      excel:
        level: 3
    signed: 2020-06-15T14:03:49+09:00
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

ネットワークを利用するサービスへのサインアップおよびサインインに用いる。
例を次に示す。

ユーザーのキーを作成する。

```sh
python -m trustx gen --signing-key ./user.signing.key \
                     --verifying-key ./user.verifying.key
```

ユーザーの検証キーを引数に設定し、サービスの nonce 取得 API をコールする。

```sh
b58_vk=`python -m trustx base58 ./user.verifying.key`
b58_nonce=`python -m trustx.examples.service "GET /auth/nonce" --verifying-key $b58_vk`
```

取得した nonce に署名し、Base58 に変換する。

```sh
b58_sig=`echo -n $b58_nonce | python -m trustx sign --signing-key ./user.signing.key | python -m trustx base58`
```

nonce 署名を引数に設定し、サービスのアクセストークン取得 API をコールする。

```sh
token=`python -m trustx.examples.service "GET /auth/token" --nonce $b58_nonce --signature $b58_sig`
```

アクセストークンを設定し、自分のプロフィール情報を取得する。

```sh
python -m trustx.examples.service "GET /profiles/me" --token $token
```

```
{
    "address": "14aynWt5xDo5Xkkw2G9bnydgBQne3hgffR"
}
```

不正なアクセスの場合。

```sh
python -m trustx.examples.service "GET /profiles/me" --token invalid
```

```
{
    "error": "Invalid token"
}
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

```python
from trustx.servers import HTTPServer
from trustx.storages import LocalStorage

HTTPServer(LocalStorage())()
```


## サーバーモジュール用 UI

- 標準のサーバーモジュール Web API 用 UI

```sh
cd ui
python -m http.server
```
