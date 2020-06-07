# Trust X

署名可能なプロフィール交換ネットワークサービス。

次のことを実現したい。

- トラストレスな署名付きの履歴書 (プロフィール)
- 他のネットワークに簡単にインポートできる
- ヒューマンフレンドリーなテキストデータに変換可能
- プロフィール情報を始めとした様々なデータへの署名機能
- 様々なモジュールを後から導入可能

プロフィールの YAML 例を次に示す。

```yaml
text: "このファイルをサービスサイトにアップロードすることで、簡単に署名付きの履歴書をインポートできます。

text: フリーテキストでアピールできる領域

skills: コンテストのスコアなどを元にレベルを振ったもの

experiences: ひとつひとつの経験を列挙

reputations: 他の人からの評判を列挙"

skills:
  word:
    level: 3
    signatures:
      ContestProvider_A: ContestProvider_A_Sig
  excel:
    level: 3
    signatures:
      ContestProvider_A: ContestProvider_A_Sig
  簿記:
    level: 3
    signatures:
      ContestProvider_B: ContestProvider_B_Sig

experiences:
  - title: 企業 A
    since: 2019-01-01
    until: 2019-12-31
    tags: [word, excel, 簿記]
    text: 神奈川県にある企業様の経理事務を担当しました。
    signatures:
      Client_A: Client_A_Sig
  - title: 知人 A
    since: 2020-01-01
    until: 2020-01-31
    tags: [word, excel, 簿記]
    text: 知人の経理事務を支援しました。
    signatures:
      Friend_A: Friend_A_Sig
  - title: 企業 B
    since: 2020-01-01
    until: 2020-12-31
    tags: [word, excel, 簿記]
    text: 埼玉県にある企業様の経理事務を担当しました。
    signatures:
      Client_B: Client_B_Sig

reputations:
  - text: とても真面目な良い方です。
    signatures:
      Client_A: Client_A_Sig
      Client_B: Client_B_Sig
  - text: この度はご支援いただき感謝します。
    signatures:
      Friend_A: Friend_A_Sig
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
