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
  signer: BASE58_ContestProviderA_Address
  data:
    word:
      level: 3
    excel:
      level: 3

BASE58_ContestProviderB_Sig_For_Skill:
  signer: BASE58_ContestProviderB_Address
  data:
    簿記:
      level: 3

BASE58_ClientA_Sig_For_Experience:
  signer: BASE58_ClientA_Address
  data:
    title: 企業 A 経理事務
    since: 2019-01-01
    until: 2019-12-31
    tags: [word, excel, 簿記]
    text: 神奈川県にある企業様の経理事務を担当しました。

BASE58_FriendA_Sig_For_Experience:
  signer: BASE58_FriendA_Address
  data:
    title: 知人 A 経理事務
    since: 2020-01-01
    until: 2020-01-31
    tags: [word, excel, 簿記]
    text: 知人の経理事務を支援しました。

BASE58_ClientB_Sig_For_Experience:
  signer: BASE58_ClientB_Address
  data:
    title: 企業 B 経理事務
    since: 2020-01-01
    until: 2020-12-31
    tags: [word, excel, 簿記]
    text: 埼玉県にある企業様の経理事務を担当しました。

BASE58_ClientA_Sig_For_Reputation:
  signer: BASE58_ClientA_Address
  data: とても真面目な良い方です。

BASE58_ClientB_Sig_For_Reputation:
  signer: BASE58_ClientB_Address
  data: とても真面目な良い方です。

BASE58_FriendA_Sig_For_Reputation:
  signer: BASE58_FriendA_Address
  data: いつも助けていただいています。ありがとう！
```

この人のスキルを証明するためのコンテスト主催者による署名例を次に示す。

```sh
cat << EOF > contests.yaml
word:
  level: 3
excel:
  level: 3
EOF
python sign.py gen | python sign.py --data contests.yaml -v
```

コマンドの出力結果は次のように得られる。

```
data (hash) 08246a01b57b08469a3f5de8d52d28d186b8b6cc110919bf95ceb827268eec71
public key a041c96ca46f01bc45b6baa0bf658b5ba95cbd04a452cf83a99caa49f48a70ae19357231f321ce127fbdd62098efda214be424f83c7e10d3ce1d1b6213393c41
public key (uncompressed, hex) 04a041c96ca46f01bc45b6baa0bf658b5ba95cbd04a452cf83a99caa49f48a70ae19357231f321ce127fbdd62098efda214be424f83c7e10d3ce1d1b6213393c41
public key (compressed, hex) 03a041c96ca46f01bc45b6baa0bf658b5ba95cbd04a452cf83a99caa49f48a70ae
address (uncompressed, b58) 1AtKbZhV5Zi9RVzjUVmKmBd9N8JgcibceZ
address (compressed, b58) 13cqFX4hQUxC8KhoPi8BWJCE2zGfhDkfyf
signature (hex) 0250a98295ae72079e91d8166fd4cd41b4764498b71d8c7292a2293e841298b9a2f4e73dea877eedcacc0a48e71de013c800858ad7f9789e6d56e0e0bd29ed9e
signature (b58) 3ghxGqpgwLFLLCx1f4c8LS5h6xgqGo56kzD8L73sG7kk4bpJmP3Uuu63cNbqcn4rr3paDrVuguW2Uq3fqKWwDo3
```

署名をキーにし、署名者のアドレスとデータを含めた YAML を作成する。

```yaml
3ghxGqpgwLFLLCx1f4c8LS5h6xgqGo56kzD8L73sG7kk4bpJmP3Uuu63cNbqcn4rr3paDrVuguW2Uq3fqKWwDo3:
  signer: 13cqFX4hQUxC8KhoPi8BWJCE2zGfhDkfyf
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
