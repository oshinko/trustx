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
BASE58_ContestProviderA_Sig_For_Skill:
  by: BASE58_ContestProviderA_Address
  data:
    word:
      level: 3
    excel:
      level: 3

BASE58_ContestProviderB_Sig_For_Skill:
  by: BASE58_ContestProviderB_Address
  data:
    簿記:
      level: 3

BASE58_ClientA_Sig_For_Experience:
  by: BASE58_ClientA_Address
  data:
    title: 企業 A 経理事務
    since: 2019-01-01
    until: 2019-12-31
    tags: [word, excel, 簿記]
    text: 神奈川県にある企業様の経理事務を担当しました。

BASE58_FriendA_Sig_For_Experience:
  by: BASE58_FriendA_Address
  data:
    title: 知人 A 経理事務
    since: 2020-01-01
    until: 2020-01-31
    tags: [word, excel, 簿記]
    text: 知人の経理事務を支援しました。

BASE58_ClientB_Sig_For_Experience:
  by: BASE58_ClientB_Address
  data:
    title: 企業 B 経理事務
    since: 2020-01-01
    until: 2020-12-31
    tags: [word, excel, 簿記]
    text: 埼玉県にある企業様の経理事務を担当しました。

BASE58_ClientA_Sig_For_Reputation:
  by: BASE58_ClientA_Address
  data: とても真面目な良い方です。

BASE58_ClientB_Sig_For_Reputation:
  by: BASE58_ClientB_Address
  data: とても真面目な良い方です。

BASE58_FriendA_Sig_For_Reputation:
  by: BASE58_FriendA_Address
  data: いつも助けていただいています。ありがとう！
```

この人のスキルを証明するためのコンテスト主催者による署名例を次に示す。

コンテスト主催者のキーを作成する。

```sh
python tool.py gen --signing-key ./contest-provider.signing.key \
                   --verifying-key ./contest-provider.verifying.key
```

ユーザーのキーを取得する。
ここでは仮のキーを作成している。

```sh
python tool.py gen --verifying-key ./user.verifying.key
```

コンテストの成績データを用意する。

```sh
cat << EOF > user.skills.yaml
word:
  level: 3
excel:
  level: 3
EOF
```

ユーザーのキーとコンテストの成績データを結合したファイルを作成する。

```sh
python tool.py concat ./user.verifying.key ./user.skills.yaml > ./user.skills.data
```

署名する。

```sh
python tool.py sign --signing-key ./contest-provider.signing.key ./user.skills.data > ./user.skills.data.sig
python tool.py base58 ./user.skills.data.sig
```

```
3nYuJp477JBDcddxtaSsKTUhcKqANmh8uP9AFPZj5ezbUZBz4uWDos3rsvupsJcDFB38p5FmXnTB4nNrH5F75NNm
```

署名を検証する。

```sh
python tool.py verify --verifying-key ./contest-provider.verifying.key \
                      --data ./user.skills.data \
                      ./user.skills.data.sig
```

```
OK
```

コンテスト主催者のアドレスを取得する。

```sh
python tool.py addr --signing-key ./contest-provider.signing.key
```

```
1LtfiUjeeZL3q4CneVAFd3M8a3wi3Sy8x9
```

ユーザーのアドレスを取得する。

```sh
python tool.py addr --verifying-key ./user.verifying.key
```

```
1NgQCSskEmtRg7xeFJnWRzt875czviaLwF
```

署名をキーにし、コンテスト主催者のアドレスとデータを含めた YAML を作成する。

ユーザーのアドレスを示す `to` は、システムの文脈から自明ならば省略できる。

```yaml
3nYuJp477JBDcddxtaSsKTUhcKqANmh8uP9AFPZj5ezbUZBz4uWDos3rsvupsJcDFB38p5FmXnTB4nNrH5F75NNm:
  by: 1LtfiUjeeZL3q4CneVAFd3M8a3wi3Sy8x9
  to: 1NgQCSskEmtRg7xeFJnWRzt875czviaLwF
  data:
    word:
      level: 3
    excel:
      level: 3
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


## 業務委託契約サポートモジュール

あくまでサポートであってデータの永続化を含め一切の責任を負わない。


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
