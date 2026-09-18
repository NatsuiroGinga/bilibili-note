---
title: "2025-Wang-LMIM-Long-Short-Period-User-Anomaly-Detection"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/2025-Wang-LMIM-Long-Short-Period-User-Anomaly-Detection.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# 基于长短周期特征的用户异常行为检测

王世谦1<sup>,</sup>2, 白宏坤2, 贾一博2, 卜飞飞2, 黄 勇1

(1. 郑州大学 网络空间安全学院 河南 郑州 450002;2. 国网河南省电力公司经济技术研究院 河南 郑州 450052)

摘要: 随着能源大数据平台用户数量与类型的不断增多 其面临的内部安全威胁也愈加突出 用户异常行为检测是抵御内部安全威胁的一种有效手段 当前主流的检测方法没有考虑同一平台内不同类型用户的行为差异以及访问行为的长短周期特征 检测性能较低 为此 利用不同类别用户的行为特点 提出长短期孤立森林模型和多时间窗口并列门循环神经网络,分别构建用户长、短周期内的访问行为特征,最后融合两种模型的结果构建一个基于用户类别的异常行为检测框架 结合某省能源大数据平台系统对所提框架进行了验证 实验结果表明 所提框架能够有效刻画平台用户的访问规律 并具有较高的异常行为识别准确率与异常处理效率

关键词: 用户行为; 异常行为检测; 长周期特征; 短周期特征

文献标志码: A

文章编号: 1671-6841(2025)06-0065-09

DOI: 10. 13705/j. issn. 1671-6841. 2024077

# Abnormal User Behavior Detection Based on Long-term and Short-term Characteristics

WANG Shiqian<sup>1,2</sup> , BAI Hongkun<sup>2</sup> , JIA Yibo<sup>2</sup> , BU Feifei<sup>2</sup> , HUANG Yong (1. School of Cyber Science and Engineering, Zhengzhou University, Zhengzhou 450002, China; 2. State Grid Henan Economic Research Institute, Zhengzhou 450052, China)

Abstract: With the increasing number and types of users, the energy big data platform is now facing prominent internal security threats. User abnormal behavior detection is an effective technique to resist such security threats. However, current mainstream detection approaches did not take behavior pattern of different types of users in the same platform and their long-term and short-term behavior characteristics in to consideration, therefore leading to low user abnormal behavior detection performance. To solve these challenges, a method was proposed to extract the long-term and short-term behavior characteristics of different users in the energy big data platform. Specifically, the long short periods isolated forest model and the multiple time windows gate recurrent neural network were proposed to construct the long-term and short-term user behavior patterns respectively, and then the results of two models were effectively integrat ed for better detection ability. Moreover, an abnormal behavior detection framework was constructed with the consideration of different platform user types. Finally, the proposed framework was verified in a provincial energy big data platform, and the experimental results showed that our framework effectively characterized different user behavior patterns in this platform and achieved a high accuracy of abnormal user behavior detection as well as high processing efficiency.

Key words: user behavior; abnormal behavior detection; long-term characteristics; short-term characteristics

## 0 引言

随着大数据技术在能源领域的不断深入,电力、燃气、石油等能源数据对国民经济发展的重要性日益凸显 因此能源大数据平台的建设受到了各级政府的高度关注 能源大数据平台不仅有助于能源企业更好地了解市场需求和资源供应情况,还能为政府部门提供决策支持和政策制定参考<sup>[</sup> <sup>1]</sup>。 然而,随着能源大数据平台的快速发展 平台用户数量不断增多、用户类型日益多样,使得平台面临的外部攻击与内部安全威胁问题愈加严峻。 但现有研究主要侧重于针对外部攻击的网络防护技术,如入侵检测、防火墙等领域 对内部安全威胁防御研究<sup>[</sup> <sup>2-</sup> <sup>3]</sup> 相对不足 在系统内部 攻击者通过非常手段 如社会工程学等方法,获得内部用户权限从而假冒合法用户,进而对平台资产进行信息搜集甚至破坏 对系统的安全运行带来了巨大的威胁。 因此,作为国家的关键信息基础设施 能源大数据平台亟须基于零信任思想对用户进行持续的认证<sup>[</sup> <sup>4-</sup> <sup>5]</sup>,加强自身应对内部安全威胁的能力

在内部威胁防御应用中 若用户的当前访问行为与历史行为特征存在较大差异,则可能意味着用户异常行为的产生 基于以上原理 国内外学者在这些领域进行了大量研究。 Nasir 等<sup>[</sup> <sup>6]</sup> 提出了基于深度学习的内部威胁检测技术 对任何偏离正常基线的行为进行检测 周娅等<sup>[</sup> <sup>7]</sup> 提出了一种基于分层欠采样和双向门控循环单元( gate recurrent unit,的恶意行为检测模型 提高了恶意评论的检测率。 周建国等<sup>[</sup> <sup>8]</sup> 使用并列门循环单元模型发现用户产生的日志异常 近年来 数字画像<sup>[</sup> <sup>9-</sup> <sup>12]</sup> 技术在内部安全威胁防御领域的应用愈加广泛 郭渊博等<sup>[</sup> <sup>13]</sup> 提出一种自动提取特征构建全细节行为画像并采用隐马尔科夫模型预测业务流程转移概率的方法,较全面地刻画了用户行为模式。 钟雅等<sup>[</sup> <sup>14]</sup> 则从人物性格等多方着手对人物进行标签画像 但是上述方法大多脱离具体的业务背景 没有考虑实际应用系统中用户的多样性和业务的差异性。

为此 本文提出一种面向能源大数据平台的用户异常行为检测方法 针对每一类型的平台用户该方法从长周期与短周期两个时间尺度对用户的平台访问行为进行特征建模 对于长周期特征 提出长短期孤立 森 林 ( long and short periods isolated for-模型 对于短周期特征 提出多时间窗口 GRU( multiple time windows GRU,MTWG) 模 型。

最后 对 与 两种模型的异常检测结果进行加权求和,并形成融合模型 LMIM(LSPIF andMTWGintegrated model）.从而提升用户异常行为的整体识别率。 最后结合某省能源大数据平台,建立一个异常检测框架并进行测试。 实验表明,公众类LMIM 的 F1 值为 96. 57%,内部类 LMIM 的 F1 值为97. 51%,表明本文提出的框架具有较高的异常行为检测准确率,并能对异常行为进行分类。

## 1 内部威胁模型

## 1. 1 能源大数据平台构架及安全威胁分析

本文基于某省能源大数据平台构架开展研究。该平台采用浏览器 服务器架构 在公开的互联网环境中对外提供能源数据相关服务 如图 所示 平台基本构架包含服务层和业务层,两者主要为能源大数据业务的正常开展提供基本软硬件支撑 另外,该能源大数据平台有一套完善的日志系统,包括用户日志 访问日志 审计日志 系统日志 安全日志和数据库日志 此外 平台的访问主体主要分为外部访问主体和内部访问主体 外部访问主体可以划分为政府 企业 公众三大类 内部访问主体可以划分为平台运维人员和管理人员。 在平台中,不同类型的用户具有不同的访问与操作权限

![](images/470b59dd610b5b21e2010dcf0b411f9b4a27df0507f22aa94108ca99b6c644fb.jpg)  
图 1 能源大数据平台架构及潜在攻击威胁  
Figure 1 Architecture of the energy big data platform and potential threats

为保障平台安全运行,系统按等级保护二级标准建设<sup>[</sup> <sup>15]</sup> 建有 等边界防护措施 能够较好地抵御来自外部的攻击 然而针对内部攻击,平台现有的边界安全设备无法起到防护作用 特别地 在内部威胁中 攻击者通过非常手段获得内部用户权限从而假冒内部合法用户进行非法活动,是较难防范的。

## 1. 2 内部攻击模式分析

针对内部攻击,本文梳理了以下几种可能存在的攻击模式。

模式一:信息搜集模式一。 外部攻击者通过非法手段,如欺骗、木马等,获得平台的访问权限后,在平台内进行资产摸排,信息搜集<sup>[</sup> <sup>16]</sup>。

模式二:信息搜集模式二。 获取平台访问权限后,攻击者利用自身的黑客技术,构造欺骗数据包,从平台获取信息

模式三 内网渗透模式 获取平台访问权限后攻击者利用自身的黑客技术,试图上传文件、执行跨站脚本 上传木马获取系统权限等

模式四:信息泄漏模式。 恶意合法用户在平台内进行资产摸排 信息搜集 泄漏平台信息

模式五:基于 APT<sup>[</sup> <sup>17]</sup> ( advanced persistent threat)的信息窃取模式 恶意用户刻意隐藏自己的异常行为特征,刻意模仿其他正常用户的行为,试图绕过态势监测系统、行为监测系统等,以达到搜集信息的目的。

## 2 异常行为检测系统总体设计

## 2. 1 设计原理

传统的异常行为检测方案仅从单一时间周期衡量用户行为特征的变化 无法适应能源大数据平台中内部攻击模式在时间跨度上的多变特性 为此本文观察到 平台用户的访问行为可以表现为长周期行为与短周期行为 长周期行为反映用户经常性的平台访问状态,这些状态包括工作时间和地点、工作条件等,具有在较长时间内保持不变的特性。 短周期行为代表了当前访问活动的动作 资源请求等情况,反映了用户在临近一段时间内的行为特征,与用户的平台权限、业务范围具有极强的关联。 因此,为进行有效的异常行为检测 需要从长周期与短周期两个时间维度构建用户访问平台的行为模式

此外 现有异常行为检测方案大都面向单类型的系统用户。 然而,能源大数据平台包含政府、企业 公众 运维人员与管理员等多种类型的访问主体。 由于不同类型用户所需要的业务不同,不同用户之间的正常行为也存在较大的区别。 举例来说,在长周期上 管理员用户的工作时间与地点与公众用户的访问时间与地点存在明显差异 而在短周期上 管理员用户操作系统管理接口的行为序列与公众用户访问一般资源接口时的行为序列也存在显著不同 因此 针对不同类型的平台用户 需要建立各自的正常行为模型与判决机制。

## 2. 2 系统结构

基于以上原理 本文提出一种基于多模型融合的用户异常行为检测系统,能够准确鉴别平台用户的访问行为 并有效适应能源大数据平台用户类型多样性的特征 如图 所示 所提系统包含用户行为特征提取和用户异常行为检测两个主要模块 本系统作为平台的一个子系统 通过日志系统获取用户的历史行为数据 系统将平台用户分为政府 企业 公众和内部四大类 分别构建不同类型用户的正常行为模型 从而建立对应的安全基线 在运行阶段 系统从日志系统中获得实时用户访问行为数据并建立当前时刻用户的长短周期行为序列,并根据用户的类型 将行为特征序列输入对应的检测模型从而实现对异常行为的快速准确检测

![](images/8a06937fd048332e79cad987ea8ec69d3a07d9e7e8ebcc840a183304c9fbda1d.jpg)  
图 2 用户异常行为检测系统  
Figure 2 System architecture of abnormal user behavior detection

## 3 用户行为特征提取

如图 2 所示,所提系统的输入数据来源于能源大数据平台的日志系统,基于获取的日志数据,对相关属性进行筛选 分别构建用户的长周期行为特征和短周期行为特征。

## 3. 1 长周期行为特征构建

长周期行为特征反映了用户在访问平台时的经常性状态,这些状态包括 Time,Week,Source IP 等。为此,本文为用户的每一次访问构建一个长周期行为特征序列 $\boldsymbol { X } = \left( \boldsymbol { x } _ { 1 } , \boldsymbol { x } _ { 2 } , \cdots , \boldsymbol { x } _ { I } \right)$ , 其中 I 表示属性的数量。 本文选取了 10 个用户访问属性构成长周期行为特征 具体如表 所示

表 1 用户长周期行为特征属性表  
Table 1 User long-term characteristics

<table><tr><td>属性</td><td>属性名称</td><td>属性描述</td></tr><tr><td> $x_{1}$ </td><td>Time</td><td>访问时间</td></tr><tr><td> $x_{2}$ </td><td>Week</td><td>星期几标识</td></tr><tr><td> $x_{3}$ </td><td>Source IP</td><td>代表经常性的工作地点,一个业务序列以第一个源IP为主</td></tr><tr><td> $x_{4}$ </td><td>OS</td><td>用户所用主机的操作系统</td></tr><tr><td> $x_{5}$ </td><td>OS Version</td><td>用户所用主机的操作系统版本</td></tr><tr><td> $x_{6}$ </td><td>Browser</td><td>用户所用浏览器</td></tr><tr><td> $x_{7}$ </td><td>Browser Version</td><td>用户所用浏览器版本</td></tr><tr><td> $x_{8}$ </td><td>Time Length</td><td>业务序列执行的时间长度</td></tr><tr><td> $x_{9}$ </td><td>Business Type</td><td>业务类型,由业务接口标识确定</td></tr><tr><td> $x_{10}$ </td><td>Access Number</td><td>当天内业务访问的次数</td></tr></table>

## 3. 2 短周期行为特征构建

短周期行为特征刻画了当前时刻用户在平台上的一系列操作行为,涵盖访问活动的 Hostname,等特征 为此 本文为某一固定时间窗口内的用户访问行为构建一个短周期行为特征序列$\pmb { Y } = ( \pmb { y } _ { 1 } , \pmb { y } _ { 2 } , \cdots , \pmb { y } _ { J } )$ , 其中: Y 为当前访问序列; $\boldsymbol { y } _ { j }$ 为第j 次访问行为特征向量 J 为行为序列长度 此外,用户的第j 次访问记为 ${ \bf y } _ { j } = \left( z _ { 1 } , z _ { 2 } , \cdots , z _ { K } \right)$ , 它由K 个属性构成 当检测到某一用户开始进行某一个业务时 则开始记录对应的属性序列 检测到业务停止时,则终止记录行为序列。 对记录的序列按照不同的时间窗口进行分割 在一个时间窗口内 若访问行为次数小于 J 对相应特征序列进行填充处理 若访问次数大于 J 则对相应特征序列进行截取处理 本文选取了六种访问属性作为用户的短周期行为特征 具体属性如表 所示

表 2 用户短周期行为特征属性表  
Table 2 User short-term characteristic

<table><tr><td>属性</td><td>属性名称</td><td>属性描述</td></tr><tr><td> $z_{1}$ </td><td>Hostname</td><td>业务服务器主机名</td></tr><tr><td> $z_{2}$ </td><td>Path</td><td>既是业务系统调用的接口标识,亦是用户感兴趣的数据标识</td></tr><tr><td> $z_{3}$ </td><td>Method</td><td>业务请求的方法类型</td></tr><tr><td> $z_{4}$ </td><td>Status Code</td><td>业务请求的处理结果</td></tr><tr><td> $z_{5}$ </td><td>Referer</td><td>来源页面的标识</td></tr><tr><td> $z_{6}$ </td><td>Time Interval</td><td>两次访问之间的时间间隔</td></tr></table>

## 4 用户异常行为检测

进一步 本文提出一种多模型融合的用户异常行为检测方法 一方面 利用 模型对用户长周期行为模式建模,模型对比了日周期变化与周周期变化 符合用户长周期特征变化慢的特点 另一方面 采用 模型对用户短周期行为特征建模充分对比不同时间窗口下的用户操作变化 最后将两种模型的判决结果进行融合形成 模型

## 4. 1 长周期特征检测模型

针对长周期行为特征 提出 模型构建用户的正常行为基线。 LSPIF 模型以一个用户的长周期行为特征 X 为输入 并输出 X 的异常得分 $s _ { \mathrm { L S P I F } ^ { \mathrm { ~ O ~ } } }$ 如图 3 所示,LSPIF 包含 M 个孤立森林模型,而每个孤立森林又由若干决策树构成。 其中,第 m 个孤立森林模型同样以 X 为输入,并输出自己的异常评分$s _ { m }$ 样本 X 的异常评分 s 与其在第 m 个孤立森林 $s _ { m }$ 中的判决路径长度有关,计算公式为

$$
s _ {m} = 2 ^ {- \frac {E [ h _ {m} (X) ]}{c (U)}},\tag{1}
$$

式中 $E \bigl [ h _ { _ m } ( X ) \bigr ]$ 表示 X 在第 m 个孤立森林模型中的平均路径长度 U 表示训练数据集中长周期行为特征样本的个数 c U 代表数据集中所有实例的平均路径长度 其计算公式为

$$
c (U) = 2 H (U - 1) - 2 (U - 1) / U,\tag{2}
$$

式中 H 是调和函数 并且 $H ( \ U ) = \ln ( \ U ) \ + \beta$ 其中 $\beta = 0 . 5 7 7 ~ 2 1 5 ~ 6 6 4 ~ 9$ ,为欧拉常数。 根据 $s _ { m }$ 可判断长周期行为特征 X 的异常程度 当 $E \bigl [ h _ { _ m } ( X ) \bigr ]$ 的值接近 U - 1 时, $s _ { m }$ 的值接近 0,X 越可能是正常样本。 当 $E \bigl [ h _ { _ m } ( X ) \bigr ]$ 的值接近 c(U) 时, $s _ { m }$ 的值接近 表 明 X 没 有 明 显 的 异 常 现 象 当$E \bigl [ h _ { { \scriptscriptstyle m } } ( X ) \bigr ]$ 的值接近 0 时, $s _ { m }$ 的值接近 1, X 越可能是异常情况

![](images/505bc1b165bf9347eba3485a7968c5dc66290a1f05012be901e64f5899af512d.jpg)  
图 3 基于 LSPIF 的长周期特征检测模型  
Figure 3 Abnormal behavior detection of long-term characteristics based on LSPIF

当 进行异常行为检测时 每个孤立森林模型都会给出一个异常评分结果<sup>[</sup> <sup>18-</sup> <sup>20]</sup>,将所有子模型的异常评分的平均值作为 模型的最终结果,即

$$
s _ {\text { L   S   P   I   F }} = \frac {1}{M} \times \sum_ {m = 1} ^ {M} s _ {m \circ}\tag{3}
$$

最后取一个接近 1 的 $b _ { \mathrm { \scriptscriptstyle L S P I F } }$ 值作为判断的阈值当 模型的最终得分大于阈值时 定义为异常

如图 3 所示,在模型训练阶段,为了使 LSPIF 模型学习用户的长周期行为的周期性规律,将日志系统中的用户历史访问数据以一周为单位进行划分,并用每一周的数据构建一个长周期特征数据子集随后选取 M 个不同子集 同时采用 算法训练各自的孤立森林模型 从而可以得到 M 个孤立森林子模型 通过以上训练方式 可以使 模型对比用户的日周期变化与周周期变化规律 更好地学习同一类用户的长周期访问规律

## 4. 2 短周期特征检测模型

针对短周期行为特征 本文提出 模型具体地 若以 为单位记平台当前时刻为 t 构造三种不同大小的滑动时间窗口 $T _ { \scriptscriptstyle 1 } , T _ { \scriptscriptstyle 2 }$ 和 $T _ { 3 }$ 它们所覆盖的时间范围分别为区间 $\left[ t \mathrm { ~ - ~ } \Delta _ { { \scriptscriptstyle 1 } } , t \right] , \left[ t \mathrm { ~ - ~ } \Delta _ { { \scriptscriptstyle 2 } } , t \right]$ 和 $[ t \mathrm { ~ - ~ } \Delta _ { \mathrm { ~ 3 ~ } } , t ] _ { \mathrm { ~ 0 ~ } }$ 其中, $\Delta _ { 1 } , \Delta _ { 2 }$ 和 $\Delta _ { 3 }$ 分别为三种时间窗口的长度,而它们对应的滑动步长均为 $\tau _ { \textsc { o } }$ 因此,可以分别从 $T _ { \scriptscriptstyle 1 } , T _ { \scriptscriptstyle 2 }$ 和 $T _ { 3 }$ 中提取当前时刻 t 对应的短周期特征序列为 $\boldsymbol { Y } _ { 1 } ^ { t } , \boldsymbol { Y } _ { 2 } ^ { t }$ 和 $\boldsymbol { Y } _ { 3 } ^ { t }$ 不失一般性 记当前时刻某一滑动时间窗口内的短周期特征序列为$\boldsymbol { Y } _ { i } ^ { t } \in \big [ \boldsymbol { Y } _ { 1 } ^ { t } , \boldsymbol { Y } _ { 2 } ^ { t } , \boldsymbol { Y } _ { 3 } ^ { t } \big ]$ 针对短周期特征序列 $\boldsymbol { Y } _ { i } ^ { t }$ 的异常检测 将滑动窗口在 t - τ 时刻的特征序列 $\boldsymbol { Y } _ { \mathrm { ~ } _ { i } } ^ { t \mathrm { ~ - ~ } }$ <sup>-</sup> <sup>τ</sup> 输 入对应的 模型<sup>[</sup> <sup>21]</sup> 并对 $\boldsymbol { Y } _ { \boldsymbol { i } } ^ { t }$ 进行预测 得到预测序列 $\hat { \boldsymbol Y } _ { i } ^ { t }$ 。 接着,计算预测特征序列与真实序列的误差,即该窗口下用户短周期行为的异常评分为 $\boldsymbol { e } _ { i } ^ { t }$ ,

$$
e _ {i} ^ {t} = \frac {1}{J _ {i}} \sum_ {j = 1} ^ {J _ {i}} \left(\boldsymbol {Y} _ {i} ^ {t} - \hat {\boldsymbol {Y}} _ {i} ^ {t}\right) ^ {2},\tag{4}
$$

式中 $J _ { i }$ 为第 i 种时间窗口下的访问序列长度 接着 需要计算判决阈值 $b _ { i } ,$ 若记 $N _ { \ i }$ 为从日志数据中提取的短周期特征序列的总数量,则判决阈值 $b _ { i }$ 的计算方法为

$$
b _ {i} = \bar {e} _ {i} + \alpha_ {i} \times \sqrt {\frac {1}{N _ {i} - 1} \sum_ {n = 0} ^ {N _ {i} - 1} \left(e _ {i} ^ {t - n \tau} - \bar {e} _ {i}\right) ^ {2}},\tag{5}
$$

式中 系数 $\alpha _ { i }$ 用于调整阈值的变化速率 $\bar { \boldsymbol { e } } _ { i }$ 是所有$N _ { \ i }$ 个短周期特征的平均误差。 基于上述方法,将三种滑动时间窗口内的短周期特征序列输入到三个不同的 GRU 模型,可获得三个异常评分 $e _ { 1 } ^ { t } , e _ { 2 } ^ { t }$ 和 $\boldsymbol { e } _ { 3 } ^ { t }$ , 以及对应的判决阈值 $b _ { 1 } , b _ { 2 }$ 和 $b _ { _ 3 } ,$ 。 最后,MTWG 获得最终的异常评分为

$$
s _ {\mathrm{MTWG}} = \frac {(e _ {1} ^ {t} + e _ {2} ^ {t} + e _ {3} ^ {t})}{3},\tag{6}
$$

此外,最终的判决阈值为

$$
b _ {\mathrm{MTWG}} = \frac {\left(b _ {1} + b _ {2} + b _ {3}\right)}{3},\tag{7}
$$

如果 $s _ { \mathrm { \scriptscriptstyle M T W G } } ~ > ~ b _ { \mathrm { \scriptscriptstyle M T W G } }$ , 则可判定该序列是异常的。

如图 所示 为了对 模型进行有效训练 本文将日志系统中的用户行为数据按照三种不同的窗口大小进行划分 具体地 本文分别以时间窗口大小对用户访问行为序列进行划分 得到不同窗口大小下的用户访问行为序列形成对应的特征序列数据集 接着 在同一数据集中,利用相邻的特征序列训练对应的 GRU 模型 其中 前一时刻的序列作为 模型的输入而后一时刻的序列作为模型的预测标签。 最后采用最小均方误差 ( least mean square error,LMSE) 损 失函数对 GRU 模型的参数进行训练。

![](images/fa1bdf72b7629c344b9cbc7a1c2a4aaca0425b93141b89c5c1236d3dd5ba5a6c.jpg)  
图 4 基于 MTWG 的短周期特征检测模型  
Figure 4 Abnormal behavior detection of short-term characteristics based on MTWG

## 4. 3 多模型融合

最后,本文提出 LMIM 模型,对 LSPIF 和 MTWG的输出结果进行有效融合 具体地 将两种模型对用户行为给出的异常得分采用加权平均的方式计算得到总的异常得分 首先对两种模型计算的异常评分进行归一化处理 使两个模型的计算结果的取值范围都在[0,1]区间。 依据两个模型异常行为检测的准确率对异常评分进行加权,得到 LMIM 模型最终的异常评分 $S _ { \mathrm { { _ { L M I M } } } }$ 为

$$
S _ {\mathrm{LMIM}} = S _ {\mathrm{LSPIF}} \times \frac {P _ {\mathrm{L}}}{P _ {\mathrm{L}} + P _ {\mathrm{S}}} + S _ {\mathrm{MTWG}} \times \frac {P _ {\mathrm{S}}}{P _ {\mathrm{L}} + P _ {\mathrm{S}}},\tag{8}
$$

式中 $P _ { \mathrm { ~ L ~ } }$ 是长周期特征检测模型 异常行为检测的准确率 而 $P _ { \mathrm { ~ s ~ } }$ 是短周期特征检测模型异常行为检测的准确率 另外 判决阈值也需要同样的加权处理。

## 5 实验验证

## 5. 1 实验环境

为了验证本文提出的 模型 模型 模型在异常行为检测任务中的性能 本文采用 Python 语言,使用 sklearn. ensemble 库中的 Iso-模块实现 模型 并使用 库中的 模块实现 模型 实验运行的操作系统为 Windows10, CPU 为 Intel ( R ) Core ( TM ) i5-10500 CPU @ 3.10 GHz.内存为 16.0 GB.硬盘为1 TB 固态硬盘。

## 5. 2 实验数据集

根据能源大数据平台的运行情况 对日志数据进行清理 剔除明显无关的数据 并对日志数据进行整理,依据隐私保护的要求对敏感数据进行脱敏,根据用户类别对数据进行标签处理 最终得到数据集共 21 600 条。 通过对数据集的分析,数据集中基本没有异常数据,故将所有数据标为正常数据。 这也符合异常样本高度不平衡的预期 为了测试所提模型性能 将数据集中三分之二的数据作为训练数据集,其余数据作为测试数据集。

一方面,为训练 LSPIF 模型,将训练数据集中的数据按周分割后 分别训练对应的孤立森林模型 另一方面,为实现 MTWG 模型的训练,设定训练次数为 1 500 次,优化器学习率/步长因子为 0. 000 1。此外,将训练数据集中的数据按 5 min、10 min、进行序列划分 并对模型进行训练

## 5. 3 LSPIF 模型性能

首先需要确定 LSPIF 模型中 M 值的大小。 因为没有异常数据进行测试 选取公众类与内部类用户数据中的 10%,随机扰动生成该类用户的异常数据 在其他实验参数固定的情况下 分别采用周长周期特征为公众类与内部类用户构建 模型并进行性能测试 在训练时 采用正常样本进行模型训练。 在测试时,采用全部样本进行测试。 实验结果如 图 5 所 示。 指 标 为 准 确 率 ( precision,P ) ,召回率 ( recall, R ) , 综 合 评 价 指 标 F 值 ( F1-score,F1) 与精度( accuracy,ACC) 。

![](images/440ba2d163352e215c2dea7cd26cabbc0773c4254071a963d1ae2f992ef50712.jpg)  
图 5 公众类 LSPIF 模型在不同周数下的性能对比  
Figure 5 Performance comparison of LSPIF models on public clients using different weeks of long-term characteristic

从图中可以看出 当选取 周的长周期特征时 模型就能达到较好的效果 同时 实验结果表明 能源大数据平台用户一个月的使用数据可以有效表达用户的行为习惯 从侧面说明了用户的使用习惯的改变 一般都与工作日有关 当长周期特征数量为 4 周以上时,效果并没有很大的提升 因此 在后续实验中 本文选择 周作为最佳的长周期特征数量。

## 5. 4 MTWG 模型性能

为了验证 MTWG 的性能,本文分别对公众用户数据与内部用户数据用基于 5 min、10 min、15 min 时间窗口内的短周期特征序列数据训练各自的通用模 型 然 后 用 全 部 数 据 训 练 本 文 提 出 的模型 并对相关结果进行对比 图 展示了内部用户数据的对比结果,可以看出 MTWG 在各项评价指标上相比通用模型有较大优势 体现了基于多时间窗口融合判决更能体现用户在业务行为上的特点。

![](images/b024f38c4ade92a4c325c5b88c4d7b7a3f1f44031de236dc41deb8d3c67c8de8.jpg)  
图 6 内部用户数据在不同时间间隔指标下 MTWG模型与通用 GRU 模型对比  
Figure 6 Comparison of MTWG model and general GRU models for internal user data with different time intervals

## 5. 5 用户类别对 LMIM 模型的影响

模型考虑了能源大数据平台用户类型多样的特性,对不同类型的平台用户进行分类建模。而传统的异常检测框架是不区分用户类别的 为检验专用 LMIM 模型的优势,本文建立了一个通用模型作为基线模型 具体地 将平台中公众与内部两类用户的所有数据混合在一起 并以此训练通用 模型

图 7、图 8 展示了公众与内部两类用户数据在与 测试的结果 图 展示了公众与内部两类用户数据在 测试的结果 对应数据如表 所示 测试结果表明 所提专用模型在各项评价指标上均优于通用模型 公众类 的 F 为内部类 的 F 为 而对比的通用 的 F 为 说明了本文基于能源大数据平台用户分类的先验知识构建的专用检测模型对异常行为有较好的准确率和精度

![](images/99a1a0152c636650ed1b997678bc0bce0c40df50487b926fa71b329979a700e7.jpg)  
图 7 通用 LSPIF 模型和专用 LSPIF 模型对比

Figure 7 Comparison between general LSPIF models and dedicated LSPIF models  
![](images/243f67e41734c28cb351842632f0d294243a47134405532370040749b59cdffc.jpg)  
图 8 通用 MTWG 模型和专用 MTWG 模型对比

Figure 8 Comparison between general MTWG models and dedicated MTWG models  
![](images/211774242808eccb6bf947f9bdc8975d90bd0cd524ac38acbbde7a99b557a063.jpg)  
图 9 通用 LMIM 模型和专用 LMIM 模型对比  
Figure 9 Comparison between general LMIM models an dedicated LMIM models

表 3 不同 LMIM 模型对比  
Table 3 Comparison of different LMIM model  
单位:%

<table><tr><td>模型</td><td>P</td><td>R</td><td>F1</td><td>ACC</td></tr><tr><td>公众类 LMIM</td><td>96.78</td><td>96.33</td><td>96.57</td><td>97.43</td></tr><tr><td>内部类 LMIM</td><td>97.64</td><td>96.66</td><td>97.15</td><td>97.87</td></tr><tr><td>通用 LMIM</td><td>86.89</td><td>87.48</td><td>87.19</td><td>90.36</td></tr></table>

## 5. 6 模拟演练测试

结合攻防演练的实际经验 以 节的各种攻击模式对平台进行模拟攻击,在一周内,利用合法用户身份进入平台 对平台进行了多次测试 测试结果如下。

测试一 进入平台后 在平台内随机访问目标共模拟了三个正常用户,在平台内进行随机点击,每次点击时长不定,次数不定,共形成 32 条数据,测试结果均能发现异常。

测试二 更换上机环境 进入平台 在平台内随机访问目标 模拟了两个用户 一个用户在家中完成正常的业务工作,形成两条数据;一个用户在网吧 随机访问平台内容形成三条数据 测试结果均能发现异常。

测试三:进入平台后,利用采集工具下载平台数据,形成数据 11 条,测试结果均能发现异常。

测试四 进入平台后 在平台内选择非该用户经常关心的数据 共模拟了五个用户 以三个公众用户的角色,多次访问光伏、煤炭与行业报告等主题数据 以一个政府用户 多次访问充电桩数据等 以一个企业用户,多次访问公司数据,共形成数据 15 条,测试结果均能发现异常

测试五 以管理员角色进入平台 在平台内下载数据,改普通用户的用户密码、权限,形成数据两条,测试发现异常。

本文所提检测框架均能顺利发现异常。 说明本文所提检测框架不仅可用于平时的用户异常行为发现,亦对异常行为的发现有效。

## 5. 7 检测框架测试实验

通过以上实验结果分析,本文检测框架能够检测出用户长周期特征的异常与短周期特征的异常。为了增强对异常的细节判断 设计综合决策器 即将监测到的数据 由分发器同时输给训练好的专用模型 由综合决策器对四类用户输出的四种异常检测结果进行综合决策,以判定该类别用户是否关心了其他用户的数据。

对一个公众用户数据的部分判断过程示例如表4 所示。 如果一个公众用户数据被公众 LMIM 输出为正常 而被其他 输出为异常 表明这是一个正常的公众用户 如果一个公众用户数据被公众LMIM 输出为异常,且被其他 LMIM 也输出为异常,表明该公众用户有异常行为但威胁等级低;如果一个公众用户数据被公众 输出为异常 而被某个其他 LMIM 输出为正常,表明有可能是假冒行为且威胁等级为中;如果一个公众用户数据被公众输出为异常 而被内部 输出为正常 表明有假冒行为且威胁等级高 如果一个内部用户出现异常 则将会判定为高威胁等级 具体不再示例分析。

表 4 公众用户行为异常检测判断示例  
Table 4 Example of detecting abnormal public user behaviors

<table><tr><td>模型</td><td colspan="5">公众用户数据检测结果</td></tr><tr><td>公众LMIM模型输出</td><td>正常</td><td>异常</td><td>异常</td><td>异常</td><td>异常</td></tr><tr><td>政府LMIM模型输出</td><td>异常</td><td>异常</td><td>正常</td><td>异常</td><td>异常</td></tr><tr><td>企业LMIM模型输出</td><td>异常</td><td>异常</td><td>异常</td><td>正常</td><td>异常</td></tr><tr><td>内部LMIM模型输出</td><td>异常</td><td>异常</td><td>异常</td><td>异常</td><td>正常</td></tr><tr><td>综合决策</td><td>正常的公众用户行为</td><td>异常的公众用户行为,威胁等级低</td><td>有假冒的行为,威胁等级低</td><td>有假冒的行为,威胁等级中</td><td>有假冒的行为,威胁等级高</td></tr></table>

由于每个专用 模型输出有三个结果可供分析 分别是 检测结果 检测结果与检测结果 当判断一个用户的行为异常后可以读取 的检测结果对异常进行进一步细分类 因为 和 分别对长周期特征和短周期特征进行异常行为检测 例如一个用户行为异常 同时 异常 而 正常 则有可能是由于更换工作环境而产生的异常

## 6 结语

本文提出一种面向能源大数据平台的多模型融合的用户异常行为检测方法 采用 对用户长周期特征建模,采用 MTWG 对短周期特征建模,最后融合 模型与 模型的检测结果 形成模型 本文构建了一个基于用户类别的异常行为检测框架,细化了对异常行为的分类,提升了对异常行为的处理效率 利用能源大数据平台的数据与生成的测试数据对方法的有效性进行验证 公众类 和内部类 异常行为检测的精度分别为 基于用户类别的异常行为检测框架对仿冒用户的识别率可以达到 以上 提高了异常处理效率 证明了本文方法的有效性 未来会对模型效率进行优化,对用户异常数据进行连续分析 实现对在线数据的异常行为检测

## 参考文献:

[1] 王圆圆, 白宏坤, 李文峰, 等. 能源大数据应用中心功能体系及应用场景设计 [J]. 智慧电力, 2020,48(3) : 15-21, 29.WANG Y Y, BAI H K, LI W F, et al. Function systemand application scenario design of energy big data appli-cation center[ J] . Smart power, 2020, 48( 3) : 15- 21,29.

[2] 陈清清, 苏盛, 畅广辉, 等. 电力信息物理系统内部威胁研究综述[ J] . 南方 电 网 技 术, 2022, 16( 6) : 1-13.CHEN Q Q, SU S, CHANG G H, et al. Review on theresearch of insider threat of cyber physical power system[ J] . Southern power system technology, 2022, 16( 6) :1-13.

[3] 郭世泽, 张磊, 潘雨, 等. 内部威胁发现检测方法研究综述[ J] . 数 据 采 集 与 处 理, 2022, 37 ( 3) : 488 -501.GUO S Z, ZHANG L, PAN Y, et al. Survey on insiderthreat detection method [ J ] . Journal of data acquisitionand processing, 2022, 37(3) : 488-501.

郭军利 许明洋 原浩宇 等 引入内生安全的零信任模型[ J] . 郑州 大 学 学 报 ( 理 学 版 ) , 2022, 54( 6) :51-58.GUO J L, XU M Y, YUAN H Y, et al. Introduction ofendogenous security of zero trust model [ J ] . Journal ofZhengzhou university ( natural science edition ) , 2022,54(6) : 51-58.

[5] 李益发,孔雪曼,耿宇,等. 零信任体系架构的可跨域 连续身份认证 郑州大学学报 理学版 - [2024-04-07] . https:∥doi. org/10. 13705/j. issn. 1671 - 6841.2023035. LI Y F, KONG X M, GENG Y, et al. Cross-domain continuous identity authentication of zero trust architecture [ J/OL] . Journal of Zhengzhou university( natural science edition) :1- 7[ 2024-04-07] . https:∥doi. org/10. 13705/ j. issn. 1671-6841. 2023035.

[6] NASIR R, AFZAL M, LATIF R, et al. Behavioral based insider threat detection using deep learning[ J] . IEEE access, 2021, 9: 143266-143274.

[7] 周娅, 李赛. 基于分层欠采样和 Bi-GRU 的恶意行为检测 模 型 [ J] . 计 算 机 工 程 与 设 计, 2022, 43 ( 2) :413-419.ZHOU Y, LI S. Toxic behavior detection based on hierar-chical undersampling and Bi-GRU network[ J] . Computerengineering and design, 2022, 43(2) : 413-419.

周建国 戴华 杨庚 等 基于并列 分类模型的日志异常检测方法[J]. 南京理工大学学报, 2022, 46

ZHOU J G, DAI H, YANG G, et al. Log anomaly detection method based on parallel GRU classification model [ J] . Journal of Nanjing university of science and technol ogy, 2022, 46(2) : 198-204.

[9] GUAN W L, ZHANG D L, YU H, et al. Customer load forecasting method based on the industry electricity con sumption behavior portrait [ J ] . Frontiers in energy research, 2021, 9: 742993.

[10] LIANG J F, LI T C, FAN H, et al. Construction of operation portraits based on a cloud model for power distribu tion networks [ J ] . Frontiers in energy research, 2022, 10: 872028.

[11] CIULKOWICZ M, MISIAK B, SZCZEŚNIAK D, et al The portrait of cyberchondria-a cross-sectional online study on factors related to health anxiety and cyberchon dria in Polish population during SARS-CoV-2 pandemic [ J] . International journal of environmental research and public health, 2022, 19(7) : 4347.

[ 12] MIAO R M, LI B Q. A user-portraits-based recommenda tion algorithm for traditional short video industry and se curity management of user privacy in social networks[ J] . Technological forecasting and social change, 2022, 185: 122103.

郭渊博 刘春辉 孔菁 等 内部威胁检测中用户行为模式画像方法研究[ J] . 通信 学 报, 2018, 39( 12) :141-150.GUO Y B, LIU C H, KONG J, et al. Study on user be-havior profiling in insider threat detection[ J] . Journal oncommunications, 2018, 39(12) : 141-150.

钟雅 郭渊博 刘春辉 等 内部威胁检测中用户属性画像方法与 应 用 [ J] . 计 算 机 科 学, 2020, 47( 3) :292-297.ZHONG Y, GUO Y B, LIU C H, et al. User attributesprofiling method and application in insider threat detection[ J] . Computer science, 2020, 47(3) : 292-297.

中国国家标准化管理委员会 信息安全技术网络安全等级保护基本要求:GB/T 22239-2019[ S] . 北京:中国标准出版社National Standardization Administration Information security technology baseline for classified protection of cyber-security: GB / T 22239 - 2019 [ S ] . Beijing: StandardsPress of China, 2019.

徐焱 贾晓璐 内网安全攻防 渗透测试实战指南北京 电子工业出版社 -XU Y, JIA X L. Intranet security attack and defense: apractical guide to penetration testing[ M] . Beijing: Pub-lishing House of Electronics Industry, 2020:33-90.

( 下转第 82 页)

XU X Z, LI Z T, XUE L J. Analysis and processing of CCD noise[ J] . Infrared and laser engineering, 2004, 33 (4) : 343-346, 357.

[21] 王磊. 基于 FPGA 的视频移动目标检测系统的研究与 实现[ D] . 济南: 济南大学, 2010. WANG L. Research and realization of video moving object detection system based on FPGA [ D] . Jinan: University of Jinan, 2010.

[22] TOYAMA K, KRUMM J, BRUMITT B, et al. Wallflower: principles and practice of background maintenance [ C]∥Proceedings of the Seventh IEEE International Conference on Computer Vision. Piscataway: IEEE Press, 1999: 255-261.

[23] WANG Y, JODOIN P M, PORIKLI F, et al. CDnet 2014: an expanded change detection benchmark dataset [ C ] ∥2014 IEEE Conference on Computer Vision and Pattern Recognition Workshops. Piscataway: IEEE Press, 2014: 393-400.

[24] 钟小芳, 周浩, 高志山, 等. 基于码本模型的运动阴影去除算 法 [ J] . 计 算 机 工 程, 2017, 43 ( 8) : 266 -271.

( 上接第 73 页)

[17] CHEN W X, HELU X H, JIN C J, et al. Advanced persistent threat organization identification based on software gene of malware [ J] . Transactions on emerging telecommunications technologies, 2020, 31(12) : e3884.

杨晓晖 张圣昌 基于多粒度级联孤立森林算法的异 常检测模型[ J] . 通信学报, 2019, 40(8) : 133-142. YANG X H, ZHANG S C. Anomaly detection model based on multi-grained cascade isolation forest algorithm [ J] . Journal on communications, 2019, 40 ( 8) : 133 - 142.

[19] 李新鹏, 高欣, 阎博, 等. 基于孤立森林算法的电力调度流数据异常检测方法 电网技术(4): 1447-1456.LI X P, GAO X, YAN B, et al. An approach of data a-

ZHONG X F, ZHOU H, GAO Z S, et al. Moving shadow removal algorithm based on codebook model[ J] . Comput er engineering, 2017, 43(8) : 266-271.

李晓瑜 马大中 付英杰 基于三帧差分混合高斯背景模型运动目标检测[J]. 吉林大学学报(信息科学版) , 2018, 36(4) : 414-422.LI X Y, MA D Z, FU Y J. Moving object detection usingmixed Gauss background model based on three framedifferencing[ J] . Journal of Jilin university ( informationscience edition) , 2018, 36(4) : 414-422.

孙渊 侯进 基于改进 算法的级联特征行车检 测[ J] . 计算机应用研究, 2019, 36(11) : 3481-3485. SUN Yuan, HOU Jin. Vehicle detection using cascaded feature based on improved PBAS algorithm[ J] . Applica tion research of computers, 2019, 36(11) : 3481-3485.

[27] BARNICH O, VAN DROOGENBROECK M. ViBe: a universal background subtraction algorithm for video se quences[ J ] . IEEE transactions on image processing: a publication of the IEEE signal processing society, 2011, 20(6) : 1709-1724.

nomaly detection in power dispatching streaming data based on isolation forest algorithm [ J ] . Power system technology, 2019, 43(4) : 1447-1456.

姬莉 霞 赵 耀 马 郑祎 等 基 于Attention 的数据库负载预测方法[J]. 郑州大学学报( 理学版) , 2022, 54(6) : 66-73.JI L X, ZHAO Y, MA Z Y, et al. Database workloadprediction method based on iForest-BiLSTM-Attention[ J ] . Journal of Zhengzhou university ( natural scienceedition) , 2022, 54(6) : 66-73.

[21] AL-KAHTANI M S, MEHMOOD Z, SADAD T, et al. Intrusion detection in the Internet of Things using fusion of GRU-LSTM deep learning model[ J] . Intelligent automation & soft computing, 2023, 37(2) : 2279-2290.