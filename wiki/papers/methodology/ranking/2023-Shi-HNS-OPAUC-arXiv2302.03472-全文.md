---
title: "2023-Shi-HNS-OPAUC-arXiv2302.03472"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/ranking/2023-Shi-HNS-OPAUC-arXiv2302.03472.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

(b) One-way Partial AUC

# On the Theories Behind Hard Negative Sampling for Recommendation

W<sub>e</sub>nt<sub>ao</sub> Shi <sub>s</sub>hi<sub>wen</sub>t<sub>ao</sub>123<sub>@ma</sub>il<sub>.us</sub>t<sub>c.e</sub>d<sub>u.c</sub> Uni<sub>ve</sub>r<sub>s</sub>it<sub>y o</sub>f S<sub>c</sub>i<sub>e</sub>n<sub>ce a</sub>nd Technolo<sub>gy</sub> of China H<sub>e</sub>f<sub>e</sub>i<sub>,</sub> Chin<sub>a</sub>

Jiawei Chen<sup>∗</sup> s<sup>l</sup>eepy<sup>h</sup>unt@zju.e<sup>d</sup>u.cn Z<sup>h</sup>ejiang University Han<sub>g</sub>zho<sub>u,</sub> China

Junkan<sub>g</sub> Wu j<sup>k</sup>wu0909@gmai<sup>l</sup>.com Uni<sub>ve</sub>r<sub>s</sub>it<sub>y</sub> <sub>o</sub>f S<sub>c</sub>i<sub>e</sub>n<sub>ce</sub> <sub>a</sub>nd Technolo<sub>gy</sub> of China H<sub>e</sub>f<sub>e</sub>i<sub>,</sub> Chin<sub>a</sub>

Chon<sub>g</sub>min<sub>g</sub> Gao <sup>chon</sup>g<sup>min</sup>g<sup>.</sup>g<sup>ao@</sup>g<sup>mail.com</sup> Uni<sub>ve</sub>r<sub>s</sub>it<sub>y o</sub>f S<sub>c</sub>i<sub>e</sub>n<sub>ce a</sub>nd Technolo<sub>gy</sub> of China H<sub>e</sub>f<sub>e</sub>i<sub>,</sub> Chin<sub>a</sub>

F<sub>u</sub>li F<sub>e</sub>n<sub>g</sub> f<sub>u</sub>lif<sub>eng</sub>93<sub>@gma</sub>il<sub>.com</sub> Uni<sub>ve</sub>r<sub>s</sub>it<sub>y</sub> <sub>o</sub>f S<sub>c</sub>i<sub>e</sub>n<sub>ce</sub> <sub>a</sub>nd Technolo<sub>gy</sub> of China H<sub>e</sub>f<sub>e</sub>i<sub>,</sub> Chin<sub>a</sub>

Jizhi Zhan<sub>g</sub> c<sup>d</sup>z<sup>h</sup>angjiz<sup>h</sup>i@mai<sup>l</sup>.ustc.e<sup>d</sup>u.cn Uni<sub>ve</sub>r<sub>s</sub>it<sub>y</sub> <sub>o</sub>f S<sub>c</sub>i<sub>e</sub>n<sub>ce</sub> <sub>a</sub>nd Technolo<sub>gy</sub> of China H<sub>e</sub>f<sub>e</sub>i<sub>,</sub> Chin<sub>a</sub>

Xi<sub>a</sub>n<sub>g</sub>n<sub>a</sub>n H<sub>e</sub><sup>∗</sup> xian<sub>g</sub>nan<sup>h</sup>e@<sub>g</sub>mai<sup>l</sup>.com Uni<sub>ve</sub>r<sub>s</sub>it<sub>y</sub> <sub>o</sub>f S<sub>c</sub>i<sub>e</sub>n<sub>ce</sub> <sub>a</sub>nd Technolo<sub>gy</sub> of China H<sub>e</sub>f<sub>e</sub>i<sub>,</sub> Chin<sub>a</sub>

## ABSTRACT

Ne<sub>g</sub>ative sam<sub>p</sub>lin<sub>g</sub> has been heavil<sub>y</sub> used to train recommender <sub>mo</sub>d<sub>e</sub>l<sub>s on</sub> l<sub>arge-sca</sub>l<sub>e</sub> d<sub>a</sub>t<sub>a, w</sub>h<sub>ere</sub>i<sub>n samp</sub>li<sub>ng</sub> h<sub>ar</sub>d <sub>examp</sub>l<sub>es usua</sub>ll<sub>y</sub> <sub>no</sub>t <sub>on</sub>l<sub>y acce</sub>l<sub>era</sub>t<sub>es</sub> th<sub>e convergence</sub> b<sub>u</sub>t <sub>a</sub>l<sub>so</sub> i<sub>mproves</sub> th<sub>e mo</sub>d<sub>e</sub>l <sub>accuracy.</sub> N<sub>ever</sub>th<sub>e</sub>l<sub>ess,</sub> th<sub>e reasons</sub> f<sub>or</sub> th<sub>e e</sub>f<sub>ec</sub>ti<sub>veness o</sub>f H<sub>ar</sub>d Ne<sub>g</sub>ative Sam<sub>p</sub>lin<sub>g</sub> (HNS) have not been revealed <sub>y</sub>et. In this work, <sub>we</sub> fill th<sub>e researc</sub>h <sub>gap</sub> b<sub>y con</sub>d<sub>uc</sub>ti<sub>ng</sub> th<sub>oroug</sub>h th<sub>eore</sub>ti<sub>ca</sub>l <sub>ana</sub>l<sub>yses</sub> on HNS. Firstl<sub>y, w</sub>e <sub>p</sub>ro<sub>v</sub>e that em<sub>p</sub>lo<sub>y</sub>in<sub>g</sub> HNS on the Ba<sub>y</sub>esian Personalized Rankin<sub>g</sub> (BPR) learner is e<sub>q</sub>uivalent to o<sub>p</sub>timizin<sub>g</sub> One-wa<sub>y</sub> Partial AUC (OPAUC). Concretel<sub>y</sub>, the BPR e<sub>q</sub>ui<sub>pp</sub>ed with D namic Ne ative Sam lin (DNS) is an exact estimator, while with <sub>so</sub>ft<sub>max-</sub>b<sub>ase</sub>d <sub>samp</sub>li<sub>ng</sub> i<sub>s a so</sub>ft <sub>es</sub>ti<sub>ma</sub>t<sub>or.</sub> S<sub>econ</sub>dl<sub>y, we prove</sub> th<sub>a</sub>t OPAUC h<sub>as a s</sub>tr<sub>o</sub>n<sub>ge</sub>r <sub>co</sub>nn<sub>ec</sub>ti<sub>o</sub>n <sub>w</sub>ith T<sub>op</sub>-� <sub>eva</sub>l<sub>ua</sub>ti<sub>o</sub>n m<sub>e</sub>tri<sub>cs</sub> than AUC and <sub>v</sub>erif<sub>y</sub> it <sub>w</sub>ith sim<sub>u</sub>lation ex<sub>p</sub>eriments. These anal<sub>y</sub>ses establish the theoretical foundation of HNS in o<sub>p</sub>timizin<sub>g</sub> To<sub>p</sub>-� <sub>recommen</sub>d<sub>a</sub>ti<sub>on per</sub>f<sub>ormance</sub> f<sub>or</sub> th<sub>e</sub> fi<sub>rs</sub>t ti<sub>me.</sub> O<sub>n</sub> th<sub>ese</sub> b<sub>ases,</sub> we ofer two insi<sub>g</sub>htful <sub>g</sub>uidelines for efective usa<sub>g</sub>e of HNS: 1) th<sub>e samp</sub>li<sub>ng</sub> h<sub>ar</sub>d<sub>ness s</sub>h<sub>ou</sub>ld b<sub>e con</sub>t<sub>ro</sub>ll<sub>a</sub>bl<sub>e, e.g., v</sub>i<sub>a pre-</sub>d<sub>e</sub>fi<sub>ne</sub>d h<sub>yp</sub>er-<sub>p</sub>arameters<sub>,</sub> to ada<sub>p</sub>t to diferent To<sub>p</sub>-� metrics and datasets<sub>;</sub> 2) the smaller the � we em<sub>p</sub>hasize in To<sub>p</sub>-� evaluation metrics, the h<sub>ar</sub>d<sub>er</sub> th<sub>e</sub> <sub>nega</sub>ti<sub>ve</sub> <sub>samp</sub>l<sub>es</sub> <sub>we</sub> <sub>s</sub>h<sub>ou</sub>ld d<sub>raw.</sub> E<sub>x</sub>t<sub>ens</sub>i<sub>ve</sub> <sub>exper</sub>i<sub>men</sub>t<sub>s</sub> <sub>on</sub> th<sub>ree</sub> <sub>rea</sub>l<sub>-wor</sub>ld b<sub>enc</sub>h<sub>mar</sub>k<sub>s</sub> <sub>ver</sub>if<sub>y</sub> th<sub>e</sub> t<sub>wo</sub> <sub>gu</sub>id<sub>e</sub>li<sub>nes.</sub>

## CCS CONCEPTS

• Information s<sub>y</sub>stems → Recommender s<sub>y</sub>stems.

## KEYWORDS

One-<sub>w</sub>a<sub>y</sub> Partial AUC<sub>,</sub> Ne<sub>g</sub>ati<sub>v</sub>e Sam<sub>p</sub>lin<sub>g,</sub> Distrib<sub>u</sub>tionall<sub>y</sub> Rob<sub>u</sub>st O<sub>p</sub>timization<sub>,</sub> Im<sub>p</sub>licit Feedback<sub>,</sub> Recommender S<sub>y</sub>stems

![](images/6db49f9f2339b0879b832fde37f30690060197b87d7a823b3c7b749ad67e8660.jpg)  
Fi<sub>g</sub>ure 1: The recommendation <sub>p</sub>erformance on three widel<sub>y</sub> used datasets with diferent sam<sub>p</sub>lin<sub>g</sub> strate<sub>g</sub>ies.

![](images/b44e4acf354b6cff4271e44d77364d2292377f3428e6699f8ef6aadb365521cc.jpg)  
(a) AUC

![](images/0d9d6f4bddb69bf78f281571f7252c998b90f18d44e0887dee2e4dcc5e4d4eea.jpg)  
Figure 2: (a) AUC, measures the entire area of the ROC curve. (b) OPAUC, measures partial area within an FPR range of [0, �]. AUC is a s<sub>p</sub>ecial case of OPAUC with � = 1.

## 1 INTRODUCTION

Recommendation s<sub>y</sub>stems are essential in addressin<sub>g</sub> information <sub>over</sub>l<sub>oa</sub>d b filt<sub>er</sub>i<sub>n un</sub>i<sub>n</sub>t<sub>en</sub>d<sub>e</sub>d i<sub>n</sub>f<sub>orma</sub>ti<sub>on an</sub>d h<sub>ave</sub> b<sub>ene</sub>fit<sub>e</sub>d man<sub>y</sub> hi<sub>g</sub>h-tech com<sub>p</sub>anies [7]. Ba<sub>y</sub>esian Personalized Rankin<sub>g</sub> (BPR) [29] is a common choice for learnin<sub>g</sub> recommender mod-<sub>e</sub>l<sub>s</sub> f<sub>rom</sub> i<sub>mp</sub>li<sub>c</sub>it f<sub>ee</sub>db<sub>ac</sub>k<sub>,</sub> <sub>w</sub>hi<sub>c</sub>h <sub>ran</sub>d<sub>om</sub>l<sub>y</sub> d<sub>raws</sub> <sub>nega</sub>ti<sub>ve</sub> it<sub>ems</sub> for the sake of eficienc<sub>y</sub> and a<sub>pp</sub>roximatel<sub>y</sub> o<sub>p</sub>timizes the AUC metric. However<sub>,</sub> uniforml<sub>y</sub> sam<sub>p</sub>led ne<sub>g</sub>ative items ma<sub>y</sub> not be inf<sub>orma</sub>ti<sub>ve,</sub> <sub>con</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>ng</sub> littl<sub>e</sub> t<sub>o</sub> th<sub>e</sub> <sub>gra</sub>di<sub>en</sub>t<sub>s</sub> <sub>an</sub>d th<sub>e</sub> <sub>convergence</sub> [28, 40]. To overcome this obstacle, researchers have <sub>p</sub>ro<sub>p</sub>osed man<sub>y</sub> Hard Ne<sub>g</sub>ative Sam<sub>p</sub>lin<sub>g</sub> (HNS) methods, such as D<sub>y</sub>namic Ne<sub>g</sub>ative Sam<sub>p</sub>lin<sub>g</sub> (DNS) [40] and Softmax-based Sam<sub>p</sub>lin<sub>g</sub> methods [9, 21, 33]. Su<sub>p</sub>erior to uniform sam<sub>p</sub>lin<sub>g</sub>, HNS methods oversam<sub>p</sub>le hi<sub>g</sub>h-scored ne<sub>g</sub>ative items<sub>,</sub> which are more informative with lar<sub>g</sub>e <sub>g</sub>radients and thus accelerate the conver<sub>g</sub>ence [8].

![](images/e22897edaca29868f0f1be4cc6e50b995cd436da94e22f4e44a60b66cdf41cff.jpg)  
Fi<sub>g</sub>ure 3: Two sim<sub>p</sub>le cases have the same overall rankin<sub>g</sub> <sub>per</sub>f<sub>ormance</sub> b<sub>u</sub>t dif<sub>eren</sub>t t<sub>op-ran</sub>ki<sub>ng per</sub>f<sub>ormance.</sub> Th<sub>e</sub> ROC <sub>cu</sub>r<sub>ves o</sub>f t<sub>wo cases</sub> h<sub>ave</sub> th<sub>e sa</sub>m<sub>e</sub> AUC b<sub>u</sub>t dif<sub>e</sub>r<sub>e</sub>nt OPAUC(�=0.4).

While existin<sub>g</sub> work usuall<sub>y</sub> attributes the su<sub>p</sub>erior <sub>p</sub>erformance of HNS to its better conver<sub>g</sub>ence<sub>,</sub> we find that the merits of HNS are b<sub>eyon</sub>d thi<sub>s</sub> th<sub>oug</sub>ht<sub>.</sub> T<sub>o va</sub>lid<sub>a</sub>t<sub>e</sub> it<sub>, we con</sub>d<sub>uc</sub>t <sub>emp</sub>i<sub>r</sub>i<sub>ca</sub>l <sub>ana</sub>l<sub>yses</sub> on three widel<sub>y</sub> <sub>u</sub>sed datasets in Fi<sub>gu</sub>re 1. We com<sub>p</sub>are two HNS strate<sub>g</sub>ies with a stron<sub>g</sub> baseline named Non-Sam<sub>p</sub>lin<sub>g</sub><sup>1</sup> [4] that com<sub>p</sub>utes the <sub>g</sub>radient over the whole data (includin<sub>g</sub> all ne<sub>g</sub>ative items). As such, the Non-Sam<sub>p</sub>lin<sub>g</sub> strate<sub>gy</sub> is su<sub>pp</sub>osed to conver<sub>g</sub>e to a better o<sub>p</sub>timum more stabl<sub>y</sub> [1, 5, 6, 17]. Nevertheless, to our sur<sub>p</sub>rise<sub>,</sub> both HNS strate<sub>g</sub>ies substantiall<sub>y</sub> out<sub>p</sub>erform the Non Sam<sub>p</sub>lin<sub>g</sub> strate<sub>gy</sub>. It indicates that fast conver<sub>g</sub>ence ma<sub>y</sub> not be the on<sup>l</sup>y justi<sup>fi</sup>cation <sup>f</sup>or t<sup>h</sup>e impressive per<sup>f</sup>ormance o<sup>f</sup> HNS. T<sup>h</sup>ere <sub>mus</sub>t b<sub>e o</sub>th<sub>er reasons</sub> f<sub>or</sub> it<sub>s super</sub>i<sub>or per</sub>f<sub>ormance, w</sub>hi<sub>c</sub>h <sub>mo</sub>ti<sub>va</sub>t<sub>es</sub> <sub>u</sub>s to delve into HNS and ex<sub>p</sub>lore its theoretical fo<sub>u</sub>ndation. O<sub>u</sub>r fi<sub>n</sub>di<sub>ngs</sub> <sub>are</sub> t<sub>wo</sub>f<sub>o</sub>ld<sub>:</sub>

• O<sub>p</sub>timizin<sub>g</sub> the BPR loss e<sub>q</sub>ui<sub>pp</sub>ed with HNS is e<sub>q</sub>uivalent to optimizing the One-way Partial AUC (OPAUC), whereas th<sub>e</sub> <sub>o</sub>ri<sub>g</sub>in<sub>a</sub>l BPR l<sub>oss</sub> <sub>o</sub>nl<sub>y</sub> <sub>op</sub>timiz<sub>es</sub> AUC<sub>.</sub> OPAUC <sub>pu</sub>t<sub>s</sub> <sub>a</sub> r<sub>e</sub> striction on the ran<sub>g</sub>e of false <sub>p</sub>ositive rate (FPR) ∈ [0, �] [13], as shown in Fi<sub>g</sub>ure 2(b), which em<sub>p</sub>hasizes the rankin<sub>g</sub> of to<sub>p</sub>- r<sub>a</sub>nk<sub>e</sub>d n<sub>ega</sub>ti<sub>ve</sub> it<sub>e</sub>m<sub>s.</sub> In <sub>co</sub>ntr<sub>as</sub>t<sub>,</sub> AUC i<sub>s</sub> <sub>a</sub> <sub>spec</sub>i<sub>a</sub>l <sub>case</sub> <sub>o</sub>f OPAUC(�) with � = 1, which considers the whole rankin<sub>g</sub> list. Our proof of the equivalence is based on the Distributionally Robust Optimization (DRO) framework [27] (cf. Section 3).

• Com<sub>p</sub>ared to AUC<sub>,</sub> OPAUC has a stron<sub>g</sub>er connection with T<sub>op</sub>-� m<sub>e</sub>tri<sub>cs.</sub> T<sub>o</sub> ill<sub>us</sub>tr<sub>a</sub>t<sub>e</sub> it<sub>, we co</sub>nd<sub>uc</sub>t <sub>s</sub>im<sub>u</sub>l<sub>a</sub>ti<sub>o</sub>n <sub>s</sub>t<sub>u</sub>di<sub>es</sub> with randoml<sub>y</sub> <sub>g</sub>enerated rankin<sub>g</sub> lists<sub>,</sub> showin<sub>g</sub> that OPAUC exhibits a much hi<sub>g</sub>her correlation with To<sub>p</sub>-� metrics like Recall<sub>,</sub> Precision and NDCG by tuning � (cf. Figure 6). This is because b<sub>o</sub>th OPAUC <sub>a</sub>nd T<sub>op</sub>-� m<sub>e</sub>tri<sub>cs ca</sub>r<sub>e</sub> m<sub>o</sub>r<sub>e a</sub>b<sub>ou</sub>t th<sub>e</sub> r<sub>a</sub>nkin<sub>g o</sub>f to<sub>p</sub>-ranked items<sub>,</sub> as shown in Fi<sub>g</sub>ure 3. Furthermore<sub>,</sub> we confirm th<sub>e corre</sub>l<sub>a</sub>ti<sub>on</sub> th<sub>roug</sub>h th<sub>eore</sub>ti<sub>ca</sub>l <sub>ana</sub>l<sub>ys</sub>i<sub>s</sub> th<sub>a</sub>t R<sub>eca</sub>ll<sub>@</sub>� <sub>an</sub>d P<sub>rec</sub>i<sub>s</sub>i<sub>on@</sub>� <sub>me</sub>t<sub>r</sub>i<sub>cs cou</sub>ld b<sub>e</sub> hi<sub>g</sub>h<sub>er an</sub>d l<sub>ower</sub> b<sub>oun</sub>d<sub>e</sub>d <sub>w</sub>ith <sub>a</sub> function of s<sub>p</sub>ecific OPAUC(�), res<sub>p</sub>ectivel<sub>y</sub>.

In short<sub>,</sub> o<sub>u</sub>r anal<sub>y</sub>ses re<sub>v</sub>eal that e<sub>qu</sub>i<sub>pp</sub>in<sub>g</sub> BPR <sub>w</sub>ith HNS is e<sub>qu</sub>i<sub>v</sub>alent to o<sub>p</sub>timizin<sub>g</sub> the OPAUC<sub>,</sub> leadin<sub>g</sub> to better To<sub>p</sub>-� rec ommendation performance (cf. Figure 4). Our analyses not only ex<sub>p</sub>lain the im<sub>p</sub>ressive <sub>p</sub>erformance of HNS but also shed li<sub>g</sub>ht on ho<sub>w</sub> to <sub>p</sub>erform HNS in recommendation. Gi<sub>v</sub>en the corres<sub>p</sub>on dence between To<sub>p</sub>-� evaluation metrics and OPAUC(�), we ofer two instructive <sub>g</sub>uidelines to ensure the <sub>p</sub>ractical efectiveness of

![](images/62240be56d961c385e163e6a9803e16bb02ff5d27c452b098c63f5ae89e1eacd.jpg)  
Fi<sub>g</sub>ure 4: The relationshi<sub>p</sub> amon<sub>g</sub> HNS<sub>,</sub> OPAUC measure<sub>,</sub> <sub>an</sub>d T<sub>op-</sub>� <sub>eva</sub>l<sub>ua</sub>ti<sub>on me</sub>t<sub>r</sub>i<sub>cs.</sub>

HNS<sub>.</sub> Fi<sub>rs</sub>t<sub>,</sub> th<sub>e</sub> <sub>samp</sub>li<sub>ng</sub> h<sub>ar</sub>d<sub>ness</sub> <sub>s</sub>h<sub>ou</sub>ld b<sub>e</sub> <sub>con</sub>t<sub>ro</sub>ll<sub>a</sub>bl<sub>e,</sub> <sub>e.g.,</sub> <sub>v</sub>i<sub>a</sub> <sub>p</sub>re-defined h<sub>yp</sub>er-<sub>p</sub>arameters<sub>,</sub> to ada<sub>p</sub>t to diferent To<sub>p</sub>-� metrics <sub>an</sub>d d<sub>a</sub>t<sub>ase</sub>t<sub>s.</sub> S<sub>econ</sub>d<sub>,</sub> th<sub>e</sub> <sub>sma</sub>ll<sub>er</sub> th<sub>e</sub> � <sub>we</sub> <sub>emp</sub>h<sub>as</sub>i<sub>ze</sub> i<sub>n</sub> T<sub>op-</sub>� <sub>eva</sub>l<sub>ua</sub>ti<sub>on me</sub>t<sub>r</sub>i<sub>cs,</sub> th<sub>e</sub> h<sub>ar</sub>d<sub>er</sub> th<sub>e nega</sub>ti<sub>ve samp</sub>l<sub>es we s</sub>h<sub>ou</sub>ld d<sub>raw.</sub>

Th<sub>e ma</sub>i<sub>n con</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>ons o</sub>f thi<sub>s paper are summar</sub>i<sub>ze</sub>d <sub>as</sub> f<sub>o</sub>ll<sub>ows:</sub>

• We are the first to establish the theoretical foundations for HNS: <sub>equ</sub>i<sub>pp</sub>in<sub>g</sub> BPR <sub>w</sub>ith DNS i<sub>s</sub> <sub>a</sub>n <sub>e</sub>x<sub>ac</sub>t <sub>es</sub>tim<sub>a</sub>t<sub>o</sub>r <sub>o</sub>f th<sub>e</sub> OPAUC o<sup>b</sup>jective, an<sup>d</sup> wit<sup>h</sup> so<sup>f</sup>tmax-<sup>b</sup>ase<sup>d</sup> samp<sup>l</sup>ing is a so<sup>f</sup>t estimator.

• We conduct theoretical anal<sub>y</sub>ses, simulation studies, and real wor<sup>ld</sup> experiments, to justi<sup>f</sup>y t<sup>h</sup>e connection <sup>b</sup>etween OPAUC and To<sub>p</sub>-� metrics and ex<sub>p</sub>lain the <sub>p</sub>erformance <sub>g</sub>ain of HNS.

• We <sub>p</sub>rovide two crucial <sub>g</sub>uidelines on how to <sub>p</sub>erform HNS and adjust samp<sup>l</sup>ing <sup>h</sup>ar<sup>d</sup>ness. T<sup>h</sup>e experiments on rea<sup>l</sup>-wor<sup>ld d</sup>atasets <sub>va</sub>lid<sub>a</sub>t<sub>e</sub> th<sub>e ra</sub>ti<sub>ona</sub>lit<sub>y o</sub>f th<sub>e gu</sub>id<sub>e</sub>li<sub>nes.</sub>

## 2 BACKGROUND

This section <sub>p</sub>rovides the necessar<sub>y</sub> back<sub>g</sub>round of Im<sub>p</sub>licit Feedback<sub>,</sub> Hard Ne<sub>g</sub>ati<sub>v</sub>e Sam<sub>p</sub>lin<sub>g</sub> Strate<sub>g</sub>ies<sub>,</sub> One-<sub>w</sub>a<sub>y</sub> Partial Area Under ROC Curve (OPAUC), and Distributionall<sub>y</sub> Robust O<sub>p</sub>timization (DRO) [27]. DRO is a robust learnin<sub>g</sub> framework that we will <sub>u</sub>se in s<sub>u</sub>bse<sub>qu</sub>ent sections.

## 2.1 Im<sub>p</sub>licit Feedback

The <sub>g</sub>oal of a recommender is to learn a score function �(�, �|�) to <sub>pre</sub>di<sub>c</sub>t <sub>scores o</sub>f <sub>uno</sub>b<sub>serve</sub>d it<sub>em</sub> � i<sub>n con</sub>t<sub>ex</sub>t <sub>� an</sub>d <sub>recommen</sub>d the to<sub>p</sub>-ranked items [1]. A lar<sub>g</sub>er <sub>p</sub>redicted score reflects a hi<sub>g</sub>her <sub>p</sub>reference for the item � ∈ I in a context $c \in C ^ { 2 }$ <sub>.</sub> In th<sub>e</sub> im<sub>p</sub>li<sub>c</sub>it f<sub>ee</sub>db<sub>ac</sub>k <sub>se</sub>tti<sub>ng, we can on</sub>l<sub>y o</sub>b<sub>serve pos</sub>iti<sub>ve c</sub>l<sub>ass</sub> $T _ { c } ^ { + } \subseteq T$ i<sub>n</sub> th<sub>e</sub> <sub>co</sub>nt<sub>e</sub>xt <sub>�.</sub> Th<sub>e</sub> r<sub>e</sub>m<sub>a</sub>inin<sub>g</sub> $J _ { c } ^ { - } = J \backslash J _ { c } ^ { + }$ <sub>are usua</sub>ll<sub>y cons</sub>id<sub>ere</sub>d <sub>as</sub> ne<sub>g</sub>ative items in the context <sub>�</sub>. In <sub>p</sub>ersonalized rankin<sub>g</sub> al<sub>g</sub>orithms wit<sup>h</sup> BPR <sup>l</sup>oss, t<sup>h</sup>e o<sup>b</sup>jective <sup>f</sup>unctions can <sup>b</sup>e <sup>f</sup>ormu<sup>l</sup>ate<sup>d</sup> as <sup>f</sup>o<sup>ll</sup>ows:

$$
\min _ {\theta} \sum_ {c \in C} \sum_ {i \in \mathcal {I} _ {c} ^ {+}} E _ {j \sim P _ {n s} (j | c)} \left[ \ell \left(r (c, i | \theta) - r (c, j | \theta)\right) \right],\tag{1}
$$

where � are the model <sub>p</sub>arameters, ℓ(�) is the loss function which is often defined as lo (1 + ex (−�)). $P _ { n s } ( j | c )$ d<sub>eno</sub>t<sub>es</sub> th<sub>e nega</sub>ti<sub>ve</sub> sam<sub>p</sub>lin<sub>g p</sub>robabilit<sub>y</sub> that a ne<sub>g</sub>ative item $j \in \mathcal { I } _ { c } ^ { - }$ i<sub>n</sub> th<sub>e con</sub>t<sub>ex</sub>t c is drawn. In BPR [29], each ne<sub>g</sub>ative item is assi<sub>g</sub>ned an e<sub>q</sub>ual sam<sub>p</sub>lin<sub>g</sub> <sub>p</sub>robabilit<sub>y</sub>. For HNS strate<sub>g</sub>ies<sub>,</sub> a ne<sub>g</sub>ative item with a lar<sub>g</sub>er <sub>p</sub>redicted score will have a hi<sub>g</sub>her sam<sub>p</sub>lin<sub>g</sub> <sub>p</sub>robabilit<sub>y</sub>. For ease of understandin<sub>g</sub>, we refer to [12] and define the “hardness” of a ne<sub>g</sub>ative sam<sub>p</sub>le as its <sub>p</sub>redicted score<sub>,</sub> i.e.<sub>,</sub> a ne<sub>g</sub>ative <sub>samp</sub>l<sub>e</sub> i<sub>s</sub> “h<sub>ar</sub>d<sub>er</sub>” th<sub>an</sub> <sub>ano</sub>th<sub>er</sub> <sub>w</sub>h<sub>en</sub> it<sub>s</sub> <sub>score</sub> i<sub>s</sub> l<sub>arger.</sub> I<sub>n</sub> what follows, �(�, �|�) is abbreviated as $r _ { c i }$ f<sub>or</sub> <sub>s</sub>h<sub>or</sub>t<sub>.</sub>

## 2.2 Hard Ne<sub>g</sub>ative Sam<sub>p</sub>lin<sub>g</sub> Strate<sub>g</sub>ies

Diferent from static sam<sub>p</sub>lin<sub>g</sub> like uniform and <sub>p</sub>o<sub>p</sub>ularit<sub>y</sub>-aware strate<sub>gy</sub> [10], HNS strate<sub>g</sub>ies are ada<sub>p</sub>tive both to context and rec ommender models durin<sub>g</sub> the trainin<sub>g</sub>. Here we review two widel<sub>y</sub> <sub>use</sub>d HNS <sub>s</sub>tr<sub>a</sub>t<sub>eg</sub>i<sub>es.</sub>

DNS [40] ranks the ne<sub>g</sub>ative items and oversam<sub>p</sub>les the hi<sub>g</sub>h ranked items<sup>3</sup>. The sam<sub>p</sub>lin<sub>g p</sub>robabilit<sub>y</sub> of DNS is defined as:

$$
P _ {n s} ^ {D N S} (j | c) = \left\{ \begin{array}{l l} \frac {1}{M}, & j \in S _ {\mathcal {I} _ {c} ^ {-}} ^ {\downarrow} [ 1, M ] \\ 0, & j \in o t h e r s \end{array} \right.,\tag{2}
$$

<sub>w</sub>h<sub>ere</sub> $S _ { { \cal T } _ { c } ^ { - } } ^ { \downarrow } [ 1 , M ] \subset { \cal T } _ { c } ^ { - }$ d<sub>eno</sub>t<sub>es</sub> th<sub>e su</sub>b<sub>se</sub>t <sub>o</sub>f th<sub>e</sub> t<sub>op-ran</sub>k<sub>e</sub>d � ne<sub>g</sub>ative items<sub>,</sub> i.e.<sub>,</sub> the ne<sub>g</sub>ative sam<sub>p</sub>les with to<sub>p</sub>-� lar<sub>g</sub>est <sub>p</sub>redi<sub>c</sub>t<sub>e</sub>d <sub>scores.</sub> R<sub>emar</sub>k th<sub>a</sub>t th<sub>e</sub> <sub>sma</sub>ll<sub>er</sub> th<sub>e</sub> � i<sub>s,</sub> th<sub>e</sub> h<sub>ar</sub>d<sub>er</sub> th<sub>e</sub> <sub>nega</sub>ti<sub>ve</sub> <sub>samp</sub>l<sub>es</sub> <sub>w</sub>ill b<sub>e</sub> d<sub>rawn.</sub>

Softmax-based sam<sub>p</sub>lin<sub>g</sub> is widel<sub>y</sub> used in adversarial learnin<sub>g</sub> [26, 33] and im<sub>p</sub>ortance sam<sub>p</sub>lin<sub>g</sub> [9, 21], where the<sub>y</sub> refer to soft max distribution to assi<sub>g</sub>n hi<sub>g</sub>her sam<sub>p</sub>lin<sub>g p</sub>robabilit<sub>y</sub> to hi<sub>g</sub>her <sub>score</sub>d it<sub>ems.</sub> Th<sub>e nega</sub>ti<sub>ve samp</sub>li<sub>ng pro</sub>b<sub>a</sub>bilit<sub>y can</sub> b<sub>e</sub> d<sub>e</sub>fi<sub>ne</sub>d <sub>as:</sub>

$$
\begin{array}{r} P _ {n s} ^ {S o f t m a x} (j | c) = \frac {\exp (r _ {c j} / \tau)}{\sum_ {k \in \mathcal {I} _ {c} ^ {-}} \exp (r _ {c k} / \tau)} \\ = \frac {\exp ((r _ {c j} - r _ {c i}) / \tau)}{\sum_ {k \in \mathcal {I} _ {c} ^ {-}} \exp ((r _ {c k} - r _ {c i}) / \tau)}, \end{array}\tag{3}
$$

where <sub>�</sub> is a tem<sub>p</sub>erat<sub>u</sub>re <sub>p</sub>arameter. It is noteworth<sub>y</sub> that the <sub>sma</sub>ll<sub>er</sub> th<sub>e</sub> $\boldsymbol { \tau } \mathbf { i s } ,$ th<sub>e</sub> h<sub>ar</sub>d<sub>er</sub> th<sub>e samp</sub>l<sub>es w</sub>ill b<sub>e</sub> d<sub>rawn.</sub>

## 2.3 One-<sub>w</sub>a<sub>y</sub> Partial AUC

For each context �, we can define true <sub>p</sub>ositive rates (TPR) and false <sub>p</sub>ositive rates (FPR) as

$$
T P R _ {c, \theta} (t) = \mathbf {P r} (r _ {c i} > t | i \in \mathcal {I} _ {c} ^ {+}),\tag{4}
$$

$$
F P R _ {c, \theta} (t) = \mathbf {P r} (r _ {c j} > t | j \in \mathcal {I} _ {c} ^ {-}).\tag{5}
$$

Then<sub>,</sub> for a <sub>g</sub>iven $s \in [ 0 , 1 ]$ <sub>,</sub> l<sub>e</sub>t $T P R _ { c , \theta } ^ { - 1 } ( s ) = \operatorname* { i n f } \{ t \in \mathbb { R } , T P R _ { c , \theta } ( t ) <$ �} and $F P R _ { c , \theta } ^ { - 1 } ( s ) = \operatorname* { i n f } \{ t \in \mathbb { R } , F P R _ { c , \theta } ( t ) < s \}$ <sub>.</sub> B<sub>ase</sub>d <sub>on</sub> th<sub>ese,</sub> th<sub>e</sub> AUC <sub>can</sub> b<sub>e</sub> f<sub>ormu</sub>l<sub>a</sub>t<sub>e</sub>d <sub>as</sub>

$$
\mathrm{AUC} (\theta) = \frac {1}{| C |} \sum_ {c \in C} \int_ {0} ^ {1} T P R _ {c, \theta} \left[ F P R _ {c, \theta} ^ {- 1} (s) \right] \mathrm{d} s.\tag{6}
$$

As shown in Fi<sub>g</sub>ure 2, One-wa<sub>y</sub> Partial AUC (OPAUC) onl<sub>y</sub> cares about the <sub>p</sub>erformance within a <sub>g</sub>iven false <sub>p</sub>ositive rate (FPR) ran<sub>g</sub>e [�, �]. Non-normalized OPAUC [13] is e<sub>q</sub>ual to

$$
O P A U C (\theta , \alpha , \beta) = \frac {1}{| C |} \sum_ {c \in C} \int_ {\alpha} ^ {\beta} T P R _ {c, \theta} \left[ F P R _ {c, \theta} ^ {- 1} (s) \right] d s.\tag{7}
$$

In thi<sub>s pape</sub>r<sub>, we co</sub>n<sub>s</sub>id<sub>e</sub>r th<sub>e spec</sub>i<sub>a</sub>l <sub>case o</sub>f OPAUC <sub>w</sub>ith $\alpha = 0 ;$ which is denoted as �����(�) for short. Based on the definition in E<sub>q</sub>. (7), we can have the followin<sub>g</sub> non-<sub>p</sub>arametric estimator of OPAUC(�):

$$
\widehat {O P A U C} (\beta) = \frac {1}{| C |} \sum_ {c \in C} \frac {1}{n _ {+}} \frac {1}{n _ {-}} \sum_ {i \in \mathcal {I} _ {c} ^ {+}} \sum_ {j \in S _ {\mathcal {I} _ {C}} ^ {\downarrow} [ 1, n _ {-} \cdot \beta ]} \mathbb {I} (r _ {c i} > r _ {c j}),\tag{8}
$$

<sub>w</sub>h<sub>ere</sub> $n _ { + } = | \mathcal { T } _ { c } ^ { + } |$ <sub>an</sub>d $n _ { - } = | \bar { \mathcal { I } } _ { c } ^ { - } |$ , and I(·) is an indicator function. F<sub>o</sub>r <sub>s</sub>im<sub>p</sub>li<sub>c</sub>it<sub>y,</sub> <sub>we</sub> <sub>assu</sub>m<sub>e</sub> $n _ { - } \cdot \beta$ i<sub>s</sub> <sub>a</sub> <sub>pos</sub>iti<sub>ve</sub> int<sub>ege</sub>r<sub>.</sub>

Since the OPAUC estimator in E<sub>q</sub>. (8) is non-continuous and <sub>non-</sub>dif<sub>eren</sub>ti<sub>a</sub>bl<sub>e, we usua</sub>ll<sub>y rep</sub>l<sub>ace</sub> th<sub>e</sub> i<sub>n</sub>di<sub>ca</sub>t<sub>or</sub> f<sub>unc</sub>ti<sub>on w</sub>ith a continuous surro<sub>g</sub>ate loss $L ( c , i , j ) = \ell ( r _ { c i } - r _ { c j } )$ <sub>.</sub> With <sub>su</sub>it<sub>a</sub>bl<sub>e</sub> surro<sub>g</sub>ate loss ℓ(·), maximizin<sub>g</sub> ����� (�) in E<sub>q</sub>. (8) is e<sub>q</sub>uivalent t<sub>o</sub> th<sub>e</sub> f<sub>o</sub>ll<sub>ow</sub>i<sub>ng</sub> <sub>pro</sub>bl<sub>em:</sub>

$$
\min _ {\theta} \frac {1}{| C |} \sum_ {c \in C} \frac {1}{n _ {+}} \sum_ {i \in \mathcal {I} _ {c} ^ {+}} \frac {1}{n _ {-} \cdot \beta} \sum_ {j \in S _ {\mathcal {I} _ {c} ^ {-}} ^ {\downarrow} [ 1, n _ {-} \cdot \beta ]} L (c, i, j).\tag{9}
$$

Remar<sup>k</sup> t<sup>h</sup>at t<sup>h</sup>e o<sup>b</sup>jective is <sup>d</sup>ivi<sup>d</sup>e<sup>d b</sup>y a <sup>fi</sup>xe<sup>d</sup> constant $\beta$ f<sub>or proo</sub>f<sub>,</sub> w<sup>h</sup>ic<sup>h d</sup>oes not a<sup>f</sup>ect t<sup>h</sup>e properties o<sup>f</sup> t<sup>h</sup>e o<sup>b</sup>jective <sup>f</sup>unction. For surro<sub>g</sub>ate loss ℓ(·), [16] <sub>p</sub>ro<sub>p</sub>oses a suficient condition to ensure it <sub>co</sub>n<sub>s</sub>i<sub>s</sub>t<sub>e</sub>nt f<sub>o</sub>r OPAUC m<sub>a</sub>ximiz<sub>a</sub>ti<sub>o</sub>n<sub>, w</sub>h<sub>e</sub>r<sub>e</sub> th<sub>e w</sub>id<sub>e</sub>l<sub>y use</sub>d l<sub>og</sub>i<sub>s</sub>ti<sub>c</sub> l<sub>oss</sub> $\ell ( t ) = \log ( 1 + \exp ( - t ) )$ satisfies the <sub>p</sub>ro<sub>p</sub>erties.

Additi<sub>o</sub>n<sub>a</sub>ll<sub>y,</sub> f<sub>o</sub>r <sub>co</sub>m<sub>pa</sub>ri<sub>so</sub>n <sub>a</sub>m<sub>o</sub>n<sub>g</sub> dif<sub>e</sub>r<sub>e</sub>nt $\beta ,$ <sub>we</sub> d<sub>e</sub>fi<sub>ne</sub> <sub>nor-</sub> malized OPAUC(�) followin<sub>g</sub> [24],

$$
\mathrm{OPAUC} _ {\text { norm }} (\beta) = \text { Trans } \left(\mathrm{OPAUC} (\beta)\right),\tag{10}
$$

<sub>w</sub>h<sub>ere</sub> th<sub>e norma</sub>li<sub>ze</sub>d t<sub>rans</sub>f<sub>orma</sub>ti<sub>on</sub> i<sub>s</sub> d<sub>e</sub>fi<sub>ne</sub>d <sub>as:</sub>

$$
\operatorname{Trans} (A) = \frac {1}{2} \left[ 1 + \frac {A - \min _ {\theta} A}{\max _ {\theta} A - \min _ {\theta} A} \right].\tag{11}
$$

## 2<sub>.</sub>4 Di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>ona</sub>ll<sub>y</sub> R<sub>o</sub>b<sub>us</sub>t O<sub>p</sub>ti<sub>m</sub>i<sub>za</sub>ti<sub>on</sub>

Gi<sub>v</sub>en a di<sub>v</sub>er<sub>g</sub>ence $D _ { \phi }$ between two distributions � and �, Distributionall<sub>y</sub> Robust O<sub>p</sub>timization (DRO) aims to minimize the ex<sub>p</sub>ected risk over the worst-case distribution � [19, 22, 27], where � is in a diver<sub>g</sub>ence ball around trainin<sub>g</sub> distribution �. Formall<sub>y,</sub> it can be d<sub>e</sub>fi<sub>ne</sub>d <sub>as:</sub>

$$
\begin{array}{c} \min _ {\theta} \sup _ {Q} E _ {Q} \left[ \mathcal {L} (f _ {\theta} (\mathbf {x}), y) \right] \\ s. t. D _ {\phi} (Q | | P) \leq \rho , \end{array}\tag{12}
$$

w<sup>h</sup>ere t<sup>h</sup>e <sup>h</sup><sub>yp</sub>er<sub>p</sub>arameter $\rho$ modulates the distributional shift, L is the loss function. In this <sub>p</sub>a<sub>p</sub>er<sub>,</sub> we will focus on two s<sub>p</sub>ecial diver-<sub>ge</sub>n<sub>ce</sub> m<sub>e</sub>tri<sub>cs,</sub> i<sub>.e.</sub> th<sub>e</sub> KL di<sub>ve</sub>r<sub>ge</sub>n<sub>ce</sub> $\begin{array} { r } { D _ { K L } ( Q | | P ) = \int \log ( \frac { \mathrm { d } Q } { \mathrm { d } P } ) \mathrm { d } Q } \end{array}$ [18] and the CVaR diver<sub>g</sub>ence $D _ { C V a R } ( Q | | P ) = \operatorname* { s u p } \log ( \frac { \mathrm { d } Q } { \mathrm { d } P } ) \left[ 1 4 \right]$

## 3 HARD NEGATIVE SAMPLING MEETS OPAUC

In this section<sub>,</sub> <sub>w</sub>e <sub>p</sub>ro<sub>v</sub>e that the BPR loss e<sub>qu</sub>i<sub>pp</sub>ed <sub>w</sub>ith HNS o<sub>p</sub>timizes OPAUC(�), which is the first ste<sub>p</sub> to understandin<sub>g</sub> the <sub>e</sub>f<sub>ec</sub>ti<sub>ve</sub>n<sub>ess o</sub>f HNS<sub>.</sub>

We ac<sup>h</sup>ieve t<sup>h</sup>e proo<sup>f b</sup>ase<sup>d</sup> on t<sup>h</sup>e DRO o<sup>b</sup>jective an<sup>d</sup> present the <sub>p</sub>roof outline in Fi<sub>g</sub>ure 5. Followin<sub>g</sub> the theorems <sub>p</sub>ro<sub>p</sub>osed in [41], we first show the connection between the OPAUC objective an<sup>d</sup> t<sup>h</sup>e DRO-<sup>b</sup>ase<sup>d</sup> o<sup>b</sup>jective. T<sup>h</sup>en we prove t<sup>h</sup>at t<sup>h</sup>e persona<sup>l</sup>ize<sup>d</sup> <sub>ran</sub>ki<sub>ng pro</sub>bl<sub>em</sub> $( \operatorname { E q . } \left( 1 \right) )$ e<sub>q</sub>ui<sub>pp</sub>ed with HNS is e<sub>q</sub>uivalent to the DRO-<sup>b</sup>ase<sup>d</sup> o<sup>b</sup>jective in our t<sup>h</sup>eorems.

Followin<sub>g</sub> [41], we define the DRO-based objective as:

$$
\begin{array}{c} \min _ {\theta} \frac {1}{| C |} \sum_ {c \in C} \frac {1}{n _ {+}} \sum_ {i \in \mathcal {I} _ {c} ^ {+}} \max _ {Q} E _ {Q} \left[ L (c, i, j) \right] \\ s. t. D _ {\phi} (Q | | P _ {0}) \leq \rho , \end{array}\tag{13}
$$

![](images/87116b7776041fcce8e1460b91f760c1c7f925314242befa5109932f17a41c65.jpg)  
Fi<sub>gure</sub> 5<sub>:</sub> Th<sub>e</sub> L<sub>emma</sub> 1 <sub>s</sub>h<sub>ows</sub> th<sub>e equ</sub>i<sub>va</sub>l<sub>ence</sub> b<sub>e</sub>t<sub>ween</sub> th<sub>e</sub> OPAUC estimator and DRO objective. Based on DRO objec ti<sub>v</sub>e<sub>, w</sub>e <sub>p</sub>ro<sub>v</sub>e the e<sub>q</sub>ui<sub>v</sub>alence bet<sub>w</sub>een HNS and OPAUC in Th<sub>eorem</sub> 1 <sub>an</sub>d Th<sub>eorem</sub> 2<sub>.</sub>

<sub>w</sub>h<sub>ere</sub> $P _ { 0 }$ d<sub>eno</sub>t<sub>es</sub> <sub>un</sub>if<sub>orm</sub> di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on</sub> <sub>over</sub> $\varPsi _ { c } ^ { - }$ , <sup>the</sup> <sup>h</sup>yp<sup>er</sup>p<sup>arameter</sup> $\rho$ <sub>mo</sub>d<sub>u</sub>l<sub>a</sub>t<sub>es</sub> th<sub>e</sub> d<sub>egree</sub> <sub>o</sub>f di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>ona</sub>l <sub>s</sub>hift<sub>,</sub> $D _ { \phi }$ is the diver<sub>g</sub>ence <sub>measure</sub> b<sub>e</sub>t<sub>ween</sub> di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>ons.</sub>

T<sup>h</sup>en we s<sup>h</sup>ow t<sup>h</sup>e connection <sup>b</sup>etween t<sup>h</sup>e OPAUC o<sup>b</sup>jective an<sup>d</sup> t<sup>h</sup>e DRO-<sup>b</sup>ase<sup>d</sup> o<sup>b</sup>jective t<sup>h</sup>roug<sup>h</sup> t<sup>h</sup>e <sup>f</sup>o<sup>ll</sup>owing <sup>l</sup>emma:

Lemma 1 (Theorem 1 of [41]). By choosing CVaR divergence $\begin{array} { r } { D _ { \phi } = D _ { C V a R } ( Q | | P _ { 0 } ) = \operatorname* { s u p } \log ( \frac { \mathrm { d } Q } { \mathrm { d } P _ { 0 } } ) } \end{array}$ ) and setting $\beta = e ^ { - \rho }$ , the DRObased objective (Eq. (13)) is equivalent to the $O P U A C ( \beta )$ objective (Eq. (9)).

B<sub>ase</sub>d <sub>on</sub> th<sub>e</sub> <sub>a</sub>b<sub>ove</sub> l<sub>emma,</sub> <sub>we</sub> <sub>prove</sub> th<sub>e</sub> <sub>equ</sub>i<sub>va</sub>l<sub>ence</sub> b<sub>e</sub>t<sub>ween</sub> t<sup>h</sup>e OPAUC o<sup>b</sup>jective an<sup>d</sup> t<sup>h</sup>e HNS <sup>b</sup>ase<sup>d</sup> o<sup>b</sup>jective.

Theorem 1. By choosing $P _ { n s } = P _ { n s } ^ { D N S } ,$

$$
M = n _ {-} \cdot \beta ,\tag{14}
$$

the DNS based problem $\left( E q . \ ( 1 ) \right)$ is equivalent to the �����(�) objective $( E q . ( 9 ) )$

Proof. Given Lemma 1, we just nee<sup>d</sup> to s<sup>h</sup>ow t<sup>h</sup>at DNS samp<sup>l</sup>ing based <sub>p</sub>roblem (E<sub>q</sub>. (1)) is e<sub>q</sub>uivalent to the DRO-based objective (E<sub>q</sub>. (13)).

By c<sup>h</sup>oosing CVaR <sup>d</sup>ivergence, t<sup>h</sup>en t<sup>h</sup>e DRO-<sup>b</sup>ase<sup>d</sup> o<sup>b</sup>jective (E<sub>q</sub>. (13)) reduces to [41] (usin<sub>g</sub> stron<sub>g</sub> dualit<sub>y</sub> and Theorem 4 in [30])

$$
\min _ {\theta} \min _ {\eta \geq 0} \frac {1}{| C |} \sum_ {c \in C} \frac {1}{n _ {+}} \sum_ {i \in \mathcal {I} _ {c} ^ {+}} \left\{\frac {1}{e ^ {- \rho}} \cdot E _ {j \sim P _ {0}} \left[ (L (c, i, j) - \eta_ {i}) _ {+} \right] + \eta_ {i} \right\},\tag{15}
$$

<sub>w</sub>h<sub>ere</sub> $P _ { 0 }$ d<sub>eno</sub>t<sub>es un</sub>if<sub>orm</sub> di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on over</sub> $ { \mathcal { T } } _ { c } ^ { - }$ . Followin<sub>g</sub> [39], it’s <sub>easy</sub> t<sub>o see</sub> th<sub>a</sub>t th<sub>e op</sub>ti<sub>ma</sub>l $\eta _ { i }$ i<sub>s</sub> th<sub>e</sub> $e ^ { - \rho }$ <sub>-quan</sub>til<sub>e o</sub>f $L ( c , i , j )$ ), which i<sub>s</sub> d<sub>e</sub>fi<sub>ne</sub>d <sub>as:</sub>

$$
\eta_ {i} ^ {*} = \inf _ {\eta_ {i}} \{P _ {j \sim P _ {0}} [ L (c, i, j) > \eta_ {i} ] <   e ^ {- \rho} \}.\tag{16}
$$

S<sub>u</sub>b<sub>s</sub>tit<sub>u</sub>t<sub>e</sub> $\eta _ { i }$ <sub>w</sub>ith $\boldsymbol { \eta } _ { i } ^ { * }$ in E<sub>q</sub>. (15) and re<sub>p</sub>lace $e ^ { - \rho }$ <sub>w</sub>ith $\scriptstyle { \frac { M } { n _ { - } } }$ <sub>,</sub> th<sub>en</sub> <sub>we</sub> obtain the e<sub>q</sub>uivalence between DNS sam<sub>p</sub>lin<sub>g</sub> based <sub>p</sub>roblem $( \operatorname { E q }$ (1)) and DRO-based objective (E<sub>q</sub>. (13)). Recall the conclusion in Lemma 1<sub>,</sub> then we com<sub>p</sub>lete the <sub>p</sub>roof b<sub>y</sub> settin<sub>g</sub> $M = n _ { - } \cdot \beta .$ □

R<sub>emar</sub>k<sub>:</sub> Th<sub>e</sub> DNS b<sub>ase</sub>d <sub>pro</sub>bl<sub>em</sub> i<sub>s an exac</sub>t b<sub>u</sub>t <sub>non-smoo</sub>th estimator of OPUAC(�), which is consistent for OPAUC(�) max imization. The h<sub>yp</sub>er<sub>p</sub>arameter � in DNS strate<sub>gy</sub> directl<sub>y</sub> d<sub>e</sub>t<sub>erm</sub>i<sub>nes</sub> $\beta$ in the OPAUC objective.

Theorem 2. By choosing $P _ { n s } = P _ { n s } ^ { S o f t m a x }$

$$
\tau = \sqrt {\frac {\operatorname{Var} _ {j} (L (c , i , j))}{- 2 \log \beta}},\tag{17}
$$

$$
\mathrm{Var} _ {j} (L (c, i, j)) = E _ {j \sim P _ {0}} \left[ \left(L (c, i, j) - E _ {j \sim P _ {0}} [ L (c, i, j) ]\right) ^ {2} \right],\tag{18}
$$

then problem (Eq. (1)) equipped with softmax-based sampling strategy is a surrogate version ofthe �����(�) objective $( E q . ( 9 ) )$ .

Th<sub>e p</sub>r<sub>oo</sub>f <sub>p</sub>r<sub>ocess</sub> i<sub>s s</sub>imil<sub>a</sub>r t<sub>o</sub> Th<sub>eo</sub>r<sub>e</sub>m 1<sub>.</sub> S<sub>u</sub>b<sub>s</sub>tit<sub>u</sub>t<sub>e</sub> CV<sub>a</sub>R diver<sub>g</sub>ence with KL diver<sub>g</sub>ence but remain the same $\rho ,$ t<sup>h</sup>en we <sub>g</sub>et a soft estimator of OPAUC(�). We <sub>p</sub>rove that the soft estimator is e<sub>q</sub>uivalent to softmax-based sam<sub>p</sub>lin<sub>g p</sub>roblem (E<sub>q</sub>. (1)). The <sub>p</sub>recise <sub>re</sub>l<sub>a</sub>ti<sub>ons</sub>hi<sub>p</sub> b<sub>e</sub>t<sub>ween</sub> <sub>�</sub> <sub>an</sub>d $\beta$ i<sub>s</sub> <sub>comp</sub>l<sub>ex</sub> <sub>an</sub>d h<sub>ar</sub>d t<sub>o</sub> <sub>compu</sub>t<sub>e.</sub> Hence we <sub>g</sub>et an a<sub>pp</sub>roximate version via the Ta<sub>y</sub>lor ex<sub>p</sub>ansion. Th<sub>e</sub> d<sub>e</sub>t<sub>a</sub>il<sub>e</sub>d <sub>proo</sub>f <sub>can</sub> b<sub>e</sub> f<sub>oun</sub>d i<sub>n</sub> A<sub>ppen</sub>di<sub>x</sub> A<sub>.</sub>

Remark: The BPR loss e<sub>q</sub>ui<sub>pp</sub>ed with softmax-based sam<sub>p</sub>lin<sub>g</sub> is a smooth but inexact estimator of OPAUC(�). The h<sub>yp</sub>er<sub>p</sub>a-<sub>rame</sub>t<sub>er</sub> <sub>�</sub> i<sub>n</sub> <sub>so</sub>ft<sub>max-</sub>b<sub>ase</sub>d <sub>samp</sub>li<sub>ng</sub> di<sub>rec</sub>tl<sub>y</sub> d<sub>e</sub>t<sub>erm</sub>i<sub>nes</sub> $\beta$ in OPAUC objective.

## 4 OPAUC MEETS TOP-K METRICS

In this section, we investi<sub>g</sub>ate the connection between OPAUC(�) and To<sub>p</sub>-� e<sub>v</sub>al<sub>u</sub>ation metrics<sub>,</sub> <sub>w</sub>hich is the second ste<sub>p</sub> to <sub>u</sub>nderstandin<sub>g</sub> the efectiveness of HNS. We <sub>p</sub>ro<sub>p</sub>ose two ar<sub>g</sub>uments to d<sub>ec</sub>l<sub>are</sub> th<sub>e</sub>i<sub>r re</sub>l<sub>a</sub>ti<sub>ons</sub>hi<sub>p:</sub>

(1) Compared to AUC, OPAUC(�) has a stronger correlati<sub>on w</sub>ith T<sub>o -</sub>� <sub>eva</sub>l<sub>ua</sub>ti<sub>on me</sub>t<sub>r</sub>i<sub>cs.</sub>

(2) A smaller � in To<sub>p</sub>-� evaluation metrics has a stronger correlation with a smaller � in OPAUC(�).

We conduct theoretical anal<sub>y</sub>sis and simulation ex<sub>p</sub>eriments to <sub>ver</sub>if<sub>y</sub> <sub>our</sub> <sub>proposa</sub>l<sub>s</sub> <sub>as</sub> f<sub>o</sub>ll<sub>ows.</sub>

## 4<sub>.</sub>1 Th<sub>eo</sub>r<sub>e</sub>ti<sub>ca</sub>l An<sub>a</sub>l<sub>ys</sub>i<sub>s</sub>

In this subsection, we anal<sub>y</sub>ze the connection between OPAUC(�) and To<sub>p</sub>-� metrics from a theoretical <sub>p</sub>ers<sub>p</sub>ective. To be concrete<sub>,</sub> <sub>we</sub> <sub>prove</sub> th<sub>a</sub>t <sub>g</sub>i<sub>ven</sub> �<sub>,</sub> P<sub>rec</sub>i<sub>s</sub>i<sub>on@</sub>� <sub>an</sub>d R<sub>eca</sub>ll<sub>@</sub>� <sub>are</sub> hi<sub>g</sub>h<sub>er</sub> bounded and lower bounded b<sub>y</sub> the functions of s<sub>p</sub>ecific OPAUC(�).

Theorem 3. Suppose there are $N _ { + }$ positive items and �<sub>−</sub> negative items, where $N _ { + } > K$ and $N _ { - } > K .$ . For any permutation ofall items in descending order, we have

$$
\begin{array}{r l r}&&{\frac {1}{N _ {+}} \left\lfloor \frac {N _ {+} + K - \sqrt {(N _ {+} + K) ^ {2} - 4 N _ {+} N _ {-} \times O P A U C (\beta)}}{2} \right\rfloor}\\&&{\leq R e c a l l @ K \leq \frac {1}{N _ {+}} \left\lceil \sqrt {N _ {+} N _ {-} \times O P A U C (\beta)} \right\rceil ,}\end{array}\tag{19}
$$

$$
\begin{array}{r l}&{\frac {1}{K} \left\lfloor \frac {N _ {+} + K - \sqrt {(N _ {+} + K) ^ {2} - 4 N _ {+} N _ {-} \times O P A U C (\beta)}}{2} \right\rfloor}\\&{\qquad \leq P r e c i s i o n @ K \leq \frac {1}{K} \left\lceil \sqrt {N _ {+} N _ {-} \times O P A U C (\beta)} \right\rceil ,}\end{array}\tag{20}
$$

where $\begin{array} { r } { \beta = \frac { K } { N _ { - } } } \end{array}$

Remark: From above<sub>,</sub> we <sub>g</sub>et the followin<sub>g</sub> ins<sub>p</sub>irations:

![](images/df4a8422c84e4561a9f59f0c008ec6980179b74f916bd05f3aec3274b3ac9cd6.jpg)  
Fi <sub>ure</sub> 6<sub>:</sub> Th<sub>e es</sub>ti<sub>ma</sub>t<sub>e</sub>d <sub>corre</sub>l<sub>a</sub>ti<sub>on coe</sub>fi<sub>c</sub>i<sub>en</sub>t b<sub>e</sub>t<sub>ween</sub> T<sub>o -</sub>� <sub>eva</sub>l<sub>ua</sub>ti<sub>on me</sub>t<sub>r</sub>i<sub>cs an</sub>d $\mathbf { O P A U C } _ { n o r m } ( \beta )$ <sub>un</sub>d<sub>er</sub> M<sub>on</sub>t<sub>e</sub> C<sub>ar</sub>l<sub>o sam-</sub> <sub>p</sub>lin<sub>g</sub> ex<sub>p</sub>eriments<sub>,</sub> where $N _ { + } = 2 0 0$ <sub>an</sub>d $N _ { - } = 8 0 0$ <sub>.</sub> W<sub>e</sub> hi hli ht th<sub>e va</sub>l<sub>ue o</sub>f $\dot { \boldsymbol { { \beta } } }$ <sub>w</sub>h<sub>en eac</sub>h <sub>curve reac</sub>h<sub>es</sub> it<sub>s max</sub>i<sub>mum corre</sub>l<sub>a</sub>ti<sub>on</sub> coeficient. Remark that AUC is also a s<sub>p</sub>ecial case of $\mathbf { O P A U C } _ { n o r m } ( \beta )$ <sub>w</sub>ith $\beta = 1$

(1) The To<sub>p</sub>-� metrics like Precision@� and Recall@� have a stron<sub>g</sub> connection with s<sub>p</sub>ecific OPAUC(�), where $\beta \ = \ \frac { K } { N _ { - } }$ H<sub>owever,</sub> <sub>suc</sub>h <sub>a</sub> <sub>connec</sub>ti<sub>on</sub> d<sub>oes</sub> <sub>no</sub>t <sub>ex</sub>i<sub>s</sub>t f<sub>or</sub> AUC<sub>,</sub> <sub>w</sub>hi<sub>c</sub>h <sub>con</sub> firms our first ar<sub>g</sub>ument. Hence, maximizin<sub>g</sub> s<sub>p</sub>ecific OPAUC(�) <sub>approx</sub>i<sub>ma</sub>t<sub>e</sub>l<sub>y</sub> <sub>op</sub>ti<sub>m</sub>i<sub>zes</sub> <sub>spec</sub>ifi<sub>c</sub> P<sub>rec</sub>i<sub>s</sub>i<sub>on@</sub>� <sub>an</sub>d R<sub>eca</sub>ll<sub>@</sub>�<sub>.</sub>

(2) The smaller the � is, the smaller the $\begin{array} { r } { \beta ( = \frac { K } { N _ { - } } ) } \end{array}$ <sub>s</sub>h<sub>ou</sub>ld b<sub>e con</sub> <sub>s</sub>id<sub>ere</sub>d<sub>.</sub> A <sub>sma</sub>ll<sub>er</sub> � h<sub>as</sub> <sub>a</sub> <sub>s</sub>t<sub>ronger</sub> <sub>connec</sub>ti<sub>on</sub> <sub>w</sub>ith <sub>a</sub> <sub>sma</sub>ll<sub>er</sub> $\beta ,$ <sub>w</sub>hi<sub>c</sub>h <sub>e</sub>f<sub>ec</sub>ti<sub>ve</sub>l<sub>y</sub> <sub>ver</sub>ifi<sub>es</sub> <sub>our</sub> <sub>secon</sub>d <sub>argumen</sub>t<sub>.</sub>

## 4<sub>.</sub>2 Si<sub>mu</sub>l<sub>a</sub>ti<sub>on</sub> E<sub>xper</sub>i<sub>men</sub>t<sub>s</sub>

In this subsection<sub>,</sub> we conduct Monte Carlo sam<sub>p</sub>lin<sub>g</sub> ex<sub>p</sub>eriments to anal ze the connection between OPAUC(�) and To -� evaluation metrics. For com<sub>p</sub>arison amon<sub>g</sub> diferent $\beta ,$ <sub>we use norma</sub>li<sub>ze</sub>d OPAUC defined in E<sub>q</sub>. (10) here. Su<sub>pp</sub>ose there are $N _ { + }$ <sub>pos</sub>iti<sub>ve</sub> it<sub>ems an</sub>d $N _ { - }$ ne<sub>g</sub>ative items in the item set I. Due to the vast scale of the entire <sub>p</sub>ermutation s<sub>p</sub>ace of items<sub>,</sub> it is im<sub>p</sub>ossible to <sub>enumera</sub>t<sub>e a</sub>ll <sub>cases</sub> f<sub>or ana</sub>l<sub>yses</sub> di<sub>rec</sub>tl<sub>y.</sub> H<sub>ence, we ma</sub>k<sub>e a</sub> M<sub>on</sub>t<sub>e-</sub> Carlo a<sub>pp</sub>roximation and uniforml<sub>y</sub> sam<sub>p</sub>le <sub>p</sub>ermutations from the <sub>space as s</sub>i<sub>mu</sub>l<sub>a</sub>t<sub>e</sub>d <sub>ran</sub>ki<sub>ng</sub> li<sub>s</sub>t<sub>s</sub> 100000 ti<sub>mes.</sub> Th<sub>en we ca</sub>l<sub>cu</sub>l<sub>a</sub>t<sub>e</sub> th<sub>e</sub> evaluation metrics (To<sub>p</sub>-� metrics and $\mathrm { O P A U C } _ { n o r m } ( \beta ) )$ f<sub>or</sub> th<sub>ese</sub> <sub>s</sub>i<sub>mu</sub>l<sub>a</sub>t<sub>e</sub>d <sub>ran</sub>ki<sub>ng</sub> li<sub>s</sub>t<sub>s.</sub> Aft<sub>erwar</sub>d<sub>, we es</sub>ti<sub>ma</sub>t<sub>e</sub> th<sub>e corre</sub>l<sub>a</sub>ti<sub>on</sub> coeficient bet<sub>w</sub>een To<sub>p</sub>-� metrics and $\mathrm { O P A U C } _ { n o r m } ( \beta )$ an<sup>d</sup> re<sub>p</sub>ort th<sub>e</sub>m in Fi<sub>gu</sub>r<sub>e</sub> 6<sub>.</sub> W<sub>e</sub> r<sub>epo</sub>rt $\beta \mathrm { o f O P A U C } _ { n o r m } ( \beta )$ in lo<sub>g</sub>arithmic scale. F<sub>ur</sub>th<sub>ermore,</sub> <sub>we</sub> hi<sub>g</sub>hli<sub>g</sub>ht th<sub>e</sub> <sub>va</sub>l<sub>ue</sub> <sub>o</sub>f $\beta$ <sub>w</sub>h<sub>en</sub> <sub>eac</sub>h <sub>curve</sub> <sub>reac</sub>h<sub>es</sub> it<sub>s max</sub>i<sub>mum corre</sub>l<sub>a</sub>ti<sub>on coe</sub>fi<sub>c</sub>i<sub>en</sub>t<sub>.</sub> R<sub>emar</sub>k th<sub>a</sub>t $\mathrm { O P A U C } _ { n o r m } ( 1 )$ i<sub>s equa</sub>l t<sub>o</sub> AUC<sub>.</sub>

A<sub>s</sub> <sub>s</sub>h<sub>ow</sub>n in Fi<sub>gu</sub>r<sub>e</sub> $^ { 6 , }$ <sub>we</sub> h<sub>ave</sub> th<sub>e</sub> f<sub>o</sub>ll<sub>ow</sub>i<sub>ng</sub> <sub>o</sub>b<sub>serva</sub>ti<sub>ons:</sub>

(1) The correlation coeficient of the hi<sub>g</sub>hest <sub>p</sub>oint of the curve is <sub>muc</sub>h l<sub>arger</sub> th<sub>an</sub> th<sub>e corre</sub>l<sub>a</sub>ti<sub>on coe</sub>fi<sub>c</sub>i<sub>en</sub>t <sub>w</sub>h<sub>en</sub> $\beta$ is e<sub>q</sub>ual to 1. That means most To<sub>p</sub>-� e<sub>v</sub>al<sub>u</sub>ation metrics ha<sub>v</sub>e hi<sub>g</sub>her <sub>corre</sub>l<sub>a</sub>ti<sub>on coe</sub>fi<sub>c</sub>i<sub>en</sub>t<sub>s w</sub>ith <sub>spec</sub>ifi<sub>c</sub> $\mathrm { O P A U C } _ { n o r m } ( \beta )$ (above 0.8) than AUC (under 0.4), which clearl<sub>y</sub> verifies our first ar<sub>g</sub>ument.

(2) Given a s<sub>p</sub>ecific � in To<sub>p</sub>-� metrics, the correlation coeficient <sub>w</sub>ith $\mathrm { O P A U C } _ { n o r m } ( \beta )$ <sub>ge</sub>t<sub>s</sub> th<sub>e</sub> <sub>max</sub>i<sub>mum</sub> <sub>va</sub>l<sub>ue</sub> <sub>a</sub>t <sub>a</sub> <sub>spec</sub>ifi<sub>c</sub> $\beta .$ B<sub>o</sub>th t<sub>oo</sub> l<sub>arge an</sub>d t<sub>oo sma</sub>ll $\beta$ <sub>w</sub>ill d<sub>egra</sub>d<sub>e</sub> th<sub>e corre</sub>l<sub>a</sub>ti<sub>on w</sub>ith s<sub>p</sub>ecific To<sub>p</sub>- $\mathbf { \nabla } \cdot K$ metrics.

(3) For diferent $K ,$ th<sub>e pea</sub>k <sub>o</sub>f th<sub>e curve var</sub>i<sub>es accor</sub>di<sub>ng</sub> t<sub>o</sub> $\beta .$ Th<sub>e</sub> <sub>sma</sub>ll<sub>er</sub> th<sub>e</sub> � i<sub>n</sub> th<sub>e</sub> T<sub>op-</sub>� <sub>eva</sub>l<sub>ua</sub>ti<sub>on me</sub>t<sub>r</sub>i<sub>cs,</sub> th<sub>e sma</sub>ll<sub>er</sub> th<sub>e</sub> $\beta$ th<sub>a</sub>t t<sub>a</sub>k<sub>es</sub> th<sub>e max</sub>i<sub>mum va</sub>l<sub>ue o</sub>f th<sub>e corre</sub>l<sub>a</sub>ti<sub>on coe</sub>fi<sub>c</sub>i<sub>en</sub>t<sub>.</sub> Thi<sub>s</sub> <sub>e</sub>f<sub>ec</sub>ti<sub>ve</sub>l<sub>y</sub> <sub>con</sub>fi<sub>rms</sub> <sub>our</sub> <sub>secon</sub>d <sub>argumen</sub>t<sub>.</sub>

(4) On the left side of the <sub>p</sub>eak of the curve, we find that the cor-<sub>re</sub>l<sub>a</sub>ti<sub>on</sub> <sub>coe</sub>fi<sub>c</sub>i<sub>en</sub>t <sub>o</sub>f NDCG<sub>@</sub>� d<sub>escen</sub>d<sub>s</sub> <sub>more</sub> <sub>s</sub>l<sub>ow</sub>l<sub>y</sub> th<sub>an</sub> th<sub>e o</sub>th<sub>er</sub> t<sub>wo me</sub>t<sub>r</sub>i<sub>cs.</sub> Thi<sub>s</sub> i<sub>s</sub> b<sub>ecause</sub> NDCG<sub>@</sub>� <sub>pays more</sub> <sub>a</sub>tt<sub>e</sub>nti<sub>o</sub>n t<sub>o</sub> t<sub>op</sub>-r<sub>a</sub>nk<sub>e</sub>d it<sub>e</sub>m<sub>s</sub> in T<sub>op</sub>-� it<sub>e</sub>m<sub>s.</sub>

## 5 DEEP UNDERSTANDING OF HNS

B<sub>ase</sub>d <sub>on</sub> th<sub>e</sub> <sub>argumen</sub>t<sub>s</sub> di<sub>scusse</sub>d <sub>a</sub>b<sub>ove,</sub> <sub>we</sub> <sub>ga</sub>i<sub>n</sub> <sub>a</sub> d<sub>eeper</sub> th<sub>eo-</sub> retical <sub>u</sub>nderstandin<sub>g</sub> of HNS. The BPR loss e<sub>qu</sub>i<sub>pp</sub>ed <sub>w</sub>ith HNS o<sub>p</sub>timizes OPAUC(�), which has a stron<sub>g</sub>er connection with To<sub>p</sub>-� <sub>me</sub>t<sub>r</sub>i<sub>cs.</sub> I<sub>n</sub> thi<sub>s</sub> <sub>sense,</sub> <sub>we</sub> d<sub>er</sub>i<sub>ve</sub> th<sub>e</sub> f<sub>o</sub>ll<sub>ow</sub>i<sub>ng</sub> <sub>coro</sub>ll<sub>ary:</sub>

Corollary 1. The BPR loss equipped with HNS approximately optimizes Top-� evaluation metrics, where the level of sampling hardness controls the value of�.

Moreover<sub>,</sub> we take a ste<sub>p</sub> further and <sub>p</sub>ro<sub>p</sub>ose two instructive <sub>g</sub>uidelines for efective usa<sub>g</sub>e of HNS.

(1) The sam<sub>p</sub>ling hardness should be controllable, e.g., via <sub>pre-</sub>d<sub>e</sub>fi<sub>ne</sub>d h<sub>yper-parame</sub>t<sub>ers,</sub> t<sub>o a</sub>d<sub>ap</sub>t t<sub>o</sub> dif<sub>eren</sub>t T<sub>op-</sub> � <sub>me</sub>t<sub>r</sub>i<sub>cs an</sub>d d<sub>a</sub>t<sub>ase</sub>t<sub>s.</sub>

(2) The smaller the � we em<sub>p</sub>hasize in To<sub>p</sub>-� evaluation met-<sub>r</sub>i<sub>cs,</sub> th<sub>e</sub> h<sub>ar</sub>d<sub>er</sub> th<sub>e nega</sub>ti<sub>ve samp</sub>l<sub>es we s</sub>h<sub>ou</sub>ld d<sub>raw.</sub>

M<sub>o</sub>ti<sub>va</sub>t<sub>e</sub>d b<sub>y</sub> th<sub>ese, we genera</sub>li<sub>ze</sub> th<sub>e</sub> DNS <sub>an</sub>d <sub>so</sub>ft<sub>max-</sub>b<sub>ase</sub>d sam<sub>p</sub>lin<sub>g</sub> to two controllable al<sub>g</sub>orithms DNS(�, �) and Softmax-$\mathbf { v } ( \rho , N )$ <sub>, as s</sub>h<sub>ow</sub>n in Al<sub>go</sub>rithm 1 <sub>a</sub>nd Al<sub>go</sub>rithm 2 r<sub>espec</sub>ti<sub>ve</sub>l<sub>y.</sub>

• In DNS(�, �), we utilize h<sub>yp</sub>er<sub>p</sub>arameter � to control sam<sub>p</sub>lin<sub>g</sub> hardness<sub>,</sub> where the ori<sub>g</sub>inal DNS is a s<sub>p</sub>ecial case with $M = 1$

• In Softmax- $\mathbf { \partial } \cdot \mathbf { v } ( \rho , N )$ , we <sub>p</sub>ro<sub>p</sub>ose to use an ada<sub>p</sub>tive � in E<sub>q</sub>. (17), i<sub>ns</sub>t<sub>ea</sub>d <sub>o</sub>f <sub>a</sub> fi<sub>xe</sub>d <sub>�</sub> i<sub>n</sub> $\operatorname { E q . }$ (3). H<sub>yp</sub>er<sub>p</sub>arameter $\rho$ <sub>con</sub>t<sub>ro</sub>l<sub>s</sub> th<sub>e sam-</sub> <sub>p</sub>li<sub>ng</sub> h<sub>ar</sub>d<sub>ness.</sub> Thi<sub>s</sub> <sub>ensures</sub> th<sub>a</sub>t $\beta$ o<sup>f</sup> t<sup>h</sup>e optimization o<sup>b</sup>jective $O P A U C ( \beta )$ remains the same d<sub>u</sub>rin<sub>g</sub> trainin<sub>g</sub>.

A<sub>s</sub> di<sub>scusse</sub>d<sub>,</sub> th<sub>e</sub> h<sub>ype</sub>r<sub>pa</sub>r<sub>a</sub>m<sub>e</sub>t<sub>e</sub>r<sub>s</sub> � <sub>a</sub>nd $\rho$ <sub>a</sub>f<sub>ec</sub>t h<sub>ow</sub> h<sub>ar</sub>d th<sub>e</sub> ne<sub>g</sub>ative sam<sub>p</sub>les we will draw. Besides<sub>,</sub> the size of the sam<sub>p</sub>lin<sub>g</sub> <sub>p</sub>ool � also afects the actual sam<sub>p</sub>lin<sub>g</sub> <sub>p</sub>robabilit<sub>y</sub> of ne<sub>g</sub>ative items. We conduct simulation ex<sub>p</sub>eriments to investi<sub>g</sub>ate the diference of the sam<sub>p</sub>lin<sub>g</sub> distribution under diferent <sub>p</sub>arameter settin<sub>g</sub>s. We <sub>c</sub>h<sub>oose</sub> th<sub>e</sub> <sub>user</sub> <sub>em</sub>b<sub>e</sub>ddi<sub>ngs</sub> <sub>an</sub>d it<sub>ems</sub> <sub>em</sub>b<sub>e</sub>ddi<sub>ngs</sub> f<sub>rom</sub> th<sub>e</sub> <sub>we</sub>ll<sub>-</sub> t<sub>ra</sub>i<sub>ne</sub>d <sub>mo</sub>d<sub>e</sub>l <sub>on</sub> th<sub>e</sub> G<sub>owa</sub>ll<sub>a</sub> d<sub>a</sub>t<sub>ase</sub>t <sub>an</sub>d k<sub>eep</sub> th<sub>em</sub> fi<sub>xe</sub>d<sub>.</sub> Th<sub>en,</sub> we randoml<sub>y</sub> <sub>p</sub>ick a (user, <sub>p</sub>ositive item) <sub>p</sub>air $( c , i )$ <sub>an</sub>d th<sub>en s</sub>i<sub>mu</sub>l<sub>a</sub>t<sub>e</sub> the sam<sub>p</sub>lin<sub>g</sub> <sub>p</sub>rocess 10000 times to estimate the actual sam<sub>p</sub>lin<sub>g</sub> <sub>pro</sub>b<sub>a</sub>bilit<sub>y.</sub> Th<sub>e</sub> <sub>average</sub> <sub>va</sub>l<sub>ue</sub> <sub>o</sub>f $\phi _ { c i j }$ over t<sup>h</sup>e sam<sub>p</sub><sup>li</sup>n<sub>g</sub> <sub>p</sub>rocess is a<sub>pp</sub>roximated as the actual sam<sub>p</sub>lin<sub>g</sub> <sub>p</sub>robabilit<sub>y</sub> that ne<sub>g</sub>ative item � is chosen b<sub>y</sub> <sub>p</sub>air (�, �) for trainin<sub>g</sub>. We re<sub>p</sub>ort the cumulative <sub>p</sub>robabilit<sub>y</sub> distribution under diferent <sub>p</sub>arameter settin<sub>g</sub>s in Fi<sub>g</sub>ure 7. The ne<sub>g</sub>ative items are in descendin<sub>g</sub> order w.r.t. their scores.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 DNS (M, N)

1: Initialize  $\theta$ 
2: for  $t = 1, \ldots, T$  do
3: Sample a mini-batch  $B \in D$ 
4: for  $(c, i) \in B$  do
5: Uniformly sample a mini-batch  $B_{c}' \in I_{c}^{-}, |B_{c}'| = N.$ 
6: Let  $p_{cij} = \begin{cases} \frac{1}{M}, &amp; j \in S_{B_{c}'}^{\downarrow}[1, M] \\ 0, &amp; j \in others. \end{cases}$ 
7: end for
8: Compute a gradient estimator  $\nabla_{t}$  by
 $\nabla_{t} = \frac{1}{|\mathcal{B}|} \sum_{(c,i) \in \mathcal{B}} \sum_{j \in I_{c}^{-}} p_{cij} \nabla_{\theta} L(c, i, j).$ 
9: Update  $\theta_{t+1} = \theta_{t} - \eta \nabla_{t}.$ 
10: end for
</div>

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 2 Softmax-v ( $\rho$ , N)

1: Initialize  $\theta$ 
2: for  $t = 1, \ldots, T$  do
3: Sample a mini-batch  $B \in D$ 
4: for  $(c, i) \in B$  do
5: Uniformly sample a mini-batch  $B_{c}' \in I_{c}^{-}$ ,  $|B_{c}'| = N$ .
6: Let  $p_{cij} = \begin{cases} \frac{e^{\ell(r_{ci}-r_{cj})/\tau}}{\sum_{k \in B_{c}'} e^{\ell(r_{ci}-r_{ck})/\tau}}, &amp; j \in B_{c}' \\ 0, &amp; j \in others, \end{cases}$ 
where  $\tau = \sqrt{\frac{\text{Var}_{j}(L(c,i,j))}{2\rho}}$ .
7: end for
8: Compute a gradient estimator  $\nabla_{t}$  by
 $\nabla_{t} = \frac{1}{|\mathcal{B}|} \sum_{(c,i) \in \mathcal{B}} \sum_{j \in I_{c}^{-}} p_{cij} \nabla_{\theta} L(c, i, j)$ .
9: Update  $\theta_{t+1} = \theta_{t} - \eta \nabla_{t}$ .
10: end for
</div>

Si<sub>nce</sub> it<sub>ems</sub> <sub>are</sub> i<sub>n</sub> d<sub>escen</sub>di<sub>ng</sub> <sub>or</sub>d<sub>er,</sub> <sub>we</sub> <sub>conc</sub>l<sub>u</sub>d<sub>e</sub> th<sub>a</sub>t th<sub>e</sub> f<sub>as</sub>t<sub>er</sub> th<sub>e</sub> <sub>curve</sub> <sub>r</sub>i<sub>ses,</sub> th<sub>e</sub> hi<sub>g</sub>h<sub>er</sub> th<sub>e</sub> <sub>samp</sub>li<sub>ng</sub> <sub>pro</sub>b<sub>a</sub>bilit<sub>y</sub> th<sub>e</sub> t<sub>op-ran</sub>k<sub>e</sub>d it<sub>ems are</sub> d<sub>rawn w</sub>ith<sub>.</sub> E<sub>as</sub>il<sub>y, we</sub> h<sub>ave</sub> th<sub>e</sub> f<sub>o</sub>ll<sub>ow</sub>i<sub>ng o</sub>b<sub>serva</sub>ti<sub>ons:</sub>

• Smaller � in DNS(�, �) means hi<sub>g</sub>her sam<sub>p</sub>lin<sub>g</sub> hardness.

• Lar<sub>g</sub>er � in DNS(�, �) means hi<sub>g</sub>her sam<sub>p</sub>lin<sub>g</sub> hardness.

• Lar<sub>g</sub>er <sub>�</sub> in Softmax-v(<sub>�</sub>, N) means hi<sub>g</sub>her sam<sub>p</sub>lin<sub>g</sub> hardness.

## 6 EXPERIMENTS

I<sub>n</sub> thi<sub>s sec</sub>ti<sub>on, we eva</sub>l<sub>ua</sub>t<sub>e</sub> th<sub>e mo</sub>d<sub>e</sub>l<sub>s on</sub> th<sub>ree pu</sub>bli<sub>c</sub> d<sub>a</sub>t<sub>ase</sub>t<sub>s</sub> t<sub>o</sub> fi<sub>gure</sub> <sub>ou</sub>t th<sub>e</sub> f<sub>o</sub>ll<sub>ow</sub>i<sub>ng</sub> <sub>ques</sub>ti<sub>ons:</sub>

• (Q1) How do DNS(�, �) and Softmax-v(<sub>�</sub>, �) <sub>p</sub>erform com-<sub>pare</sub>d t<sub>o s</sub>t<sub>a</sub>t<sub>e-o</sub>f<sub>-</sub>th<sub>e-ar</sub>t HNS <sub>me</sub>th<sub>o</sub>d<sub>s</sub>? I<sub>s</sub> it b<sub>ene</sub>fi<sub>c</sub>i<sub>a</sub>l t<sub>o con</sub>t<sub>ro</sub>l <sub>samp</sub>li<sub>ng</sub> h<sub>ar</sub>d<sub>ness</sub> <sub>w</sub>ith <sub>pre-</sub>d<sub>e</sub>fi<sub>ne</sub>d h<sub>yperparame</sub>t<sub>ers</sub>?

• (Q2) Can ex<sub>p</sub>eriment results validate our second <sub>g</sub>uideline on a<sup>d</sup>justing samp<sup>l</sup>ing <sup>h</sup>ar<sup>d</sup>ness accor<sup>d</sup>ing to � in Top-� metrics?

![](images/f789d9c6db14f9500d0dfafffddfa94bbcdc28f47e4cdcc1046f246d4cff6a54.jpg)  
Fi<sub>g</sub>ure 7: A<sub>pp</sub>roximated distributions under diferent <sub>p</sub>a-<sub>rame</sub>t<sub>er se</sub>tti<sub>ngs.</sub> Th<sub>e</sub> f<sub>as</sub>t<sub>er</sub> th<sub>e curve r</sub>i<sub>ses,</sub> th<sub>e</sub> hi<sub>g</sub>h<sub>er</sub> th<sub>e</sub> sam<sub>p</sub>lin<sub>g</sub> <sub>p</sub>robabilit<sub>y</sub> the to<sub>p</sub>-ranked items are drawn with.

T<sub>a</sub>bl<sub>e</sub> 1: Th<sub>e</sub> St<sub>a</sub>ti<sub>s</sub>ti<sub>cs o</sub>f D<sub>a</sub>t<sub>ase</sub>t<sub>s</sub>

<table><tr><td>Dataset</td><td>User</td><td>Item</td><td>Train</td><td>Test</td><td>Sparsity</td></tr><tr><td>Gowalla</td><td>29,858</td><td>40,988</td><td>822,358</td><td>205,106</td><td>99.9160%</td></tr><tr><td>Yelp</td><td>77,277</td><td>45,638</td><td>1,684,846</td><td>419,049</td><td>99.9403%</td></tr><tr><td>Amazon</td><td>130,380</td><td>128,939</td><td>1,934,404</td><td>481,246</td><td>99.9856%</td></tr></table>

Dataset. The Statistics of three public datasets are shown in T<sub>a</sub>bl<sub>e</sub> 1<sub>, w</sub>hi<sub>c</sub>h <sub>vary</sub> i<sub>n sca</sub>l<sub>e an</sub>d <sub>spars</sub>it<sub>y.</sub> Th<sub>e</sub> G<sub>owa</sub>ll<sub>a</sub> d<sub>a</sub>t<sub>ase</sub>t i<sub>s</sub> th<sub>e</sub> <sub>co</sub>ll<sub>ec</sub>ti<sub>on o</sub>f <sub>user c</sub>h<sub>ec</sub>k<sub>-</sub>i<sub>n</sub> hi<sub>s</sub>t<sub>or</sub>i<sub>es.</sub> Th<sub>e</sub> Y<sub>e</sub>l<sub>p</sub> d<sub>a</sub>t<sub>ase</sub>t i<sub>s a su</sub>b<sub>se</sub>t <sub>o</sub>f Y<sub>e</sub>l<sub>p</sub>’<sub>s</sub> b<sub>us</sub>i<sub>nesses,</sub> <sub>rev</sub>i<sub>ews,</sub> <sub>an</sub>d <sub>user</sub> d<sub>a</sub>t<sub>a.</sub> Th<sub>e</sub> A<sub>mazon</sub> d<sub>a</sub>t<sub>ase</sub>t i<sub>s a su</sub>b<sub>se</sub>t <sub>o</sub>f <sub>cus</sub>t<sub>o</sub>m<sub>e</sub>r<sub>s</sub>’ r<sub>a</sub>tin<sub>gs</sub> f<sub>o</sub>r Am<sub>a</sub>z<sub>o</sub>n b<sub>oo</sub>k<sub>s.</sub> C<sub>o</sub>n<sub>s</sub>id<sub>e</sub>rin<sub>g</sub> the ratin<sub>g</sub>s are inte<sub>g</sub>ers ran<sub>g</sub>in<sub>g</sub> from 1 to 5<sub>,</sub> the ratin<sub>g</sub>s above 4 are re<sub>g</sub>arded as <sub>p</sub>ositive. Followin<sub>g</sub> [9, 21], we levera<sub>g</sub>e the routine <sup>strate</sup>gy <sup>—</sup> <sup>5-core</sup> <sup>settin</sup>g <sup>to</sup> p<sup>re</sup>p<sup>rocess</sup> <sup>the</sup> <sup>dataset.</sup>

F<sub>or</sub> <sub>eac</sub>h <sub>user,</sub> <sub>we</sub> <sub>ran</sub>d<sub>om</sub>l<sub>y</sub> <sub>se</sub>l<sub>ec</sub>t 80% <sub>o</sub>f it<sub>ems</sub> t<sub>o</sub> f<sub>orm</sub> th<sub>e</sub> trainin<sub>g</sub> set and 20% of items to form the test set. 10% of the trainin<sub>g</sub> <sub>se</sub>t i<sub>s</sub> <sub>use</sub>d f<sub>or</sub> <sub>va</sub>lid<sub>a</sub>ti<sub>on.</sub> Th<sub>e</sub> <sub>mo</sub>d<sub>e</sub>l<sub>s</sub> <sub>are</sub> b<sub>u</sub>ilt <sub>on</sub> th<sub>e</sub> t<sub>ra</sub>i<sub>n</sub>i<sub>ng</sub> <sub>se</sub>t <sub>an</sub>d <sub>eva</sub>l<sub>ua</sub>t<sub>e</sub>d <sub>on</sub> th<sub>e</sub> t<sub>es</sub>t <sub>se</sub>t<sub>.</sub>

Metrics. When evaluating the models, we filter out positive items i<sub>n</sub> th<sub>e</sub> t<sub>ra</sub>i<sub>n</sub>i<sub>ng se</sub>t <sub>an</sub>d <sub>u</sub>tili<sub>ze w</sub>id<sub>e</sub>l<sub>y-use</sub>d <sub>me</sub>t<sub>r</sub>i<sub>cs</sub> R<sub>eca</sub>ll<sub>@</sub>� <sub>an</sub>d NDCG<sub>@</sub>� t<sub>o eva</sub>l<sub>ua</sub>t<sub>e</sub> th<sub>e recommen</sub>d<sub>a</sub>ti<sub>on per</sub>f<sub>ormance.</sub> Th<sub>e</sub> d<sub>e-</sub> t<sub>a</sub>il<sub>e</sub>d d<sub>e</sub>finiti<sub>o</sub>n<sub>s</sub> <sub>a</sub>r<sub>e</sub> <sub>s</sub>h<sub>ow</sub>n in A<sub>ppe</sub>ndix C<sub>.</sub>

## 6<sub>.</sub>1 B<sub>ase</sub>li<sub>nes</sub>

To verif<sub>y</sub> the efectiveness of DNS(�, �) and Softmax-v(<sub>�</sub>, �) meth-<sub>o</sub>d<sub>s,</sub> <sub>we</sub> <sub>compare</sub> <sub>our</sub> <sub>a</sub>l<sub>gor</sub>ith<sub>ms</sub> <sub>w</sub>ith th<sub>e</sub> f<sub>o</sub>ll<sub>ow</sub>i<sub>ng</sub> b<sub>ase</sub>li<sub>nes.</sub>

• BPR [29] is a classical method for im<sub>p</sub>licit feedback. It utilizes <sub>p</sub>airwise lo<sub>g</sub>it loss and randoml<sub>y</sub> sam<sub>p</sub>les ne<sub>g</sub>ative items.

• AOBPR [28] im<sub>p</sub>roves BPR throu<sub>g</sub>h ada<sub>p</sub>tivel<sub>y</sub> oversam<sub>p</sub>lin<sub>g</sub> to<sub>p</sub>-ranked ne<sub>g</sub>ative items.

• WARP [35] uses the Wei<sub>g</sub>hted A<sub>pp</sub>roximate-Rank Pairwise loss f<sub>unc</sub>ti<sub>on</sub> f<sub>or</sub> i<sub>mp</sub>li<sub>c</sub>it f<sub>ee</sub>db<sub>ac</sub>k<sub>.</sub>

• IRGAN [33] utilizes a minimax <sub>g</sub>ame to o<sub>p</sub>timize the <sub>g</sub>enerative and discriminati<sub>v</sub>e net<sub>w</sub>ork sim<sub>u</sub>ltaneo<sub>u</sub>sl<sub>y</sub>. The ne<sub>g</sub>ati<sub>v</sub>e items <sub>are</sub> d<sub>rawn</sub> b<sub>ase</sub>d <sub>on so</sub>ft<sub>max</sub> di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on.</sub>

• DNS [40] is a d<sub>y</sub>namic ne<sub>g</sub>ative sam<sub>p</sub>ler, which is a s<sub>p</sub>ecial case of DNS(�, �) with � = 1.

• Kernel [2] is an eficient sam<sub>p</sub>lin<sub>g</sub> method that a<sub>pp</sub>roximates th<sub>e so</sub>ft<sub>max</sub> di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on w</sub>ith <sub>non-nega</sub>ti<sub>ve qua</sub>d<sub>ra</sub>ti<sub>c</sub> k<sub>erne</sub>l<sub>.</sub>

• PRIS [21] utilizes im<sub>p</sub>ortance sam<sub>p</sub>lin<sub>g</sub> for trainin<sub>g</sub>, where im-<sub>p</sub>ortance wei<sub>g</sub>hts are based on softmax distribution. The<sub>y</sub> ado<sub>p</sub>t th<sub>e</sub> <sub>un</sub>if<sub>orm</sub> <sub>an</sub>d <sub>popu</sub>l<sub>ar</sub>it<sub>y-</sub>b<sub>ase</sub>d di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on</sub> t<sub>o</sub> <sub>cons</sub>t<sub>ruc</sub>t th<sub>e</sub> sam<sub>p</sub>lin<sub>g p</sub>ool, denoted as PRIS(U) and PRIS(P), res<sub>p</sub>ectivel<sub>y</sub>.

T<sub>a</sub>bl<sub>e</sub> 2<sub>:</sub> P<sub>er</sub>f<sub>ormance compar</sub>i<sub>son on</sub> th<sub>ree</sub> d<sub>a</sub>t<sub>ase</sub>t<sub>s.</sub> Th<sub>e</sub> b<sub>es</sub>t <sub>resu</sub>lt<sub>s are</sub> i<sub>n</sub> b<sub>o</sub>ld <sub>an</sub>d th<sub>e secon</sub>d b<sub>es</sub>t <sub>are un</sub>d<sub>er</sub>li<sub>ne</sub>d<sub>.</sub> Th<sub>e</sub> baselines are taken from [9], as we com<sub>p</sub>letel<sub>y</sub> follow their ex<sub>p</sub>eriment settings. “\*\*” denote the im<sub>p</sub>rovement is significant <sub>w</sub>ith t<sub>-</sub>t<sub>es</sub>t <sub>w</sub>ith $\textstyle p < 0 . 0 5$

<table><tr><td rowspan="2">Method</td><td colspan="2">Gowalla</td><td colspan="2">Yelp</td><td colspan="2">Amazon</td></tr><tr><td>NDCG@50</td><td>Recall@50</td><td>NDCG@50</td><td>Recall@50</td><td>NDCG@50</td><td>Recall@50</td></tr><tr><td>BPR</td><td>0.1216</td><td>0.2048</td><td>0.0524</td><td>0.1083</td><td>0.0499</td><td>0.1171</td></tr><tr><td>AOBPR</td><td>0.1385</td><td>0.2417</td><td>0.0677</td><td>0.1346</td><td>0.0563</td><td>0.1303</td></tr><tr><td>WARP</td><td>0.1248</td><td>0.2240</td><td>0.0636</td><td>0.1332</td><td>0.0542</td><td>0.1267</td></tr><tr><td>IRGAN</td><td>0.1443</td><td>0.2242</td><td>0.0695</td><td>0.1367</td><td>0.0627</td><td>0.1395</td></tr><tr><td>Kernel</td><td>0.1399</td><td>0.2264</td><td>0.0658</td><td>0.1315</td><td>0.0700</td><td>0.1495</td></tr><tr><td>DNS</td><td>0.1412</td><td>0.1839</td><td>0.0693</td><td>0.1425</td><td>0.0615</td><td>0.1378</td></tr><tr><td>PRIS(U)</td><td>0.1334</td><td>0.2217</td><td>0.0639</td><td>0.1273</td><td>0.0607</td><td>0.1377</td></tr><tr><td>PRIS(P)</td><td>0.1385</td><td>0.2282</td><td>0.0673</td><td>0.1342</td><td>0.0697</td><td>0.1463</td></tr><tr><td>AdaSIR(U)</td><td>0.1489</td><td>0.2500</td><td>0.0732</td><td>0.1523</td><td>0.0731</td><td>0.1505</td></tr><tr><td>AdaSIR(P)</td><td>0.1519</td><td>0.2516</td><td>0.0731</td><td>0.1525</td><td>0.0740</td><td>0.1534</td></tr><tr><td>DNS(M, N)</td><td> $\underline{0.1811^{**}}$ </td><td> $\underline{0.2989^{**}}$ </td><td> $\underline{0.0899^{**}}$ </td><td> $\underline{0.1774^{**}}$ </td><td> $\underline{0.1014^{**}}$ </td><td> $\underline{0.1833^{**}}$ </td></tr><tr><td>Softmax-v(ρ, N)</td><td> $\underline{0.1837^{**}}$ </td><td> $\underline{0.2993^{**}}$ </td><td> $\underline{0.0840^{**}}$ </td><td> $\underline{0.1690^{**}}$ </td><td> $\underline{0.1046^{**}}$ </td><td> $\underline{0.1937^{**}}$ </td></tr></table>

• AdaSIR [9] is a two-sta<sub>g</sub>e method that maintains a fixed size contextualized sam<sub>p</sub>le <sub>p</sub>ool with im<sub>p</sub>ortance resam<sub>p</sub>lin<sub>g</sub>. The im <sub>p</sub>ortance wei<sub>g</sub>hts are based on softmax distribution. The<sub>y</sub> ado<sub>p</sub>t th<sub>e</sub> <sub>un</sub>if<sub>orm</sub> <sub>an</sub>d <sub>popu</sub>l<sub>ar</sub>it<sub>y-</sub>b<sub>ase</sub>d di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on</sub> t<sub>o</sub> <sub>cons</sub>t<sub>ruc</sub>t th<sub>e</sub> sam<sub>p</sub>lin<sub>g</sub> <sub>p</sub>ool, denoted as AdaSIR(U) and AdaSIR(P), res<sub>p</sub>ectivel<sub>y</sub>.

## 6<sub>.</sub>2 I<sub>mp</sub>l<sub>emen</sub>t<sub>a</sub>ti<sub>on</sub> D<sub>e</sub>t<sub>a</sub>il<sub>s</sub>

The al<sub>g</sub>orithms are im<sub>p</sub>lemented based on P<sub>y</sub>Torch. We com<sub>p</sub>letel<sub>y</sub> follow the ex eriments settin in [9, 21]. We utilize Matrix Factor ization (MF) as the recommender model for our model. We utilize Adam o<sub>p</sub>timizer to o<sub>p</sub>timize all <sub>p</sub>arameters. The dimension of user <sub>an</sub>d it<sub>em em</sub>b<sub>e</sub>ddi<sub>ng</sub> i<sub>s se</sub>t t<sub>o</sub> 32<sub>.</sub> Th<sub>e</sub> b<sub>a</sub>t<sub>c</sub>h <sub>s</sub>i<sub>ze</sub> i<sub>s</sub> fi<sub>xe</sub>d t<sub>o</sub> 4096<sub>, an</sub>d th<sub>e</sub> l<sub>earn</sub>i<sub>ng ra</sub>t<sub>e</sub> i<sub>s se</sub>t t<sub>o</sub> 0<sub>.</sub>001 b<sub>y</sub> d<sub>e</sub>f<sub>au</sub>lt<sub>.</sub> Th<sub>e num</sub>b<sub>er o</sub>f t<sub>ra</sub>i<sub>n</sub>i<sub>ng</sub> <sub>epoc</sub>h<sub>s</sub> i<sub>s se</sub>t t<sub>o</sub> 200 f<sub>or a</sub>ll <sub>me</sub>th<sub>o</sub>d<sub>s.</sub> W<sub>e u</sub>tili<sub>ze gr</sub>id <sub>searc</sub>h t<sub>o</sub> fi<sub>n</sub>d the best with weight\_decay ∈ {0.1, 0.01, 0.001, 0.0001}. The hyper <sub>p</sub>arameter � in DNS(�, �) is tuned over {1,2,3,4,5,10,20} and the <sup>h</sup>yp<sup>er</sup>p<sup>arameter</sup> $\rho$ of Softmax-v(<sub>�</sub>, �) is tuned over {0.01, 0.1, 1, 10, 100} for all datasets. Due to the eficiency limit, the sample pool size � f<sub>or eac</sub>h <sub>user</sub> i<sub>s se</sub>t t<sub>o</sub> 200<sub>,</sub> 200<sub>, an</sub>d 500 f<sub>or</sub> G<sub>owa</sub>ll<sub>a,</sub> Y<sub>e</sub>l<sub>p, an</sub>d A<sub>ma</sub> zon. The maximum number of ne<sub>g</sub>ative sam<sub>p</sub>les <sub>p</sub>er <sub>p</sub>ositive <sub>p</sub>air (�, �) is the sam<sub>p</sub>le <sub>p</sub>ool size. The baseline results are directl<sub>y</sub> taken from [9], as we com<sub>p</sub>letel<sub>y</sub> follow their ex<sub>p</sub>eriment settin<sub>g</sub>. Code is available at htt<sub>p</sub>s://<sub>g</sub>ithub.com/swt-user/WWW<sub>\_</sub>2023<sub>\_</sub>code.

## 6.3 (RQ1) Performance Comparison

Table 2 shows the <sub>p</sub>erformance of DNS(�, �), Softmax-v(<sub>�</sub>, �), <sub>an</sub>d b<sub>ase</sub>li<sub>nes.</sub> F<sub>rom</sub> th<sub>em,</sub> <sub>we</sub> h<sub>ave</sub> th<sub>e</sub> f<sub>o</sub>ll<sub>ow</sub>i<sub>ng</sub> k<sub>ey</sub> fi<sub>n</sub>di<sub>ngs:</sub>

• Com<sub>p</sub>ared to the uniform ne<sub>g</sub>ative sam<sub>p</sub>lin<sub>g</sub> method BPR, most HNS methods <sub>p</sub>erform much better, es<sub>p</sub>eciall<sub>y</sub> DNS(�, �) and Softmax-v(<sub>�</sub>, �). This clearl<sub>y</sub> verifies the efectiveness of HNS.

• Benefitin<sub>g</sub> from the adjustable sam<sub>p</sub>lin<sub>g</sub> hardness, DNS(�, �) si<sub>g</sub> nificantl<sub>y</sub> out<sub>p</sub>erform its ori<sub>g</sub>inal version on avera<sub>g</sub>e 40%. Mean <sub>w</sub>hil<sub>e,</sub> th<sub>e</sub> t<sub>wo</sub> <sub>me</sub>th<sub>o</sub>d<sub>s</sub> <sub>a</sub>l<sub>so</sub> <sub>presen</sub>t <sub>a</sub> h<sub>uge</sub> <sub>per</sub>f<sub>ormance</sub> b<sub>oos</sub>t <sub>over o</sub>th<sub>er</sub> HNS <sub>me</sub>th<sub>o</sub>d<sub>s.</sub> Th<sub>ese</sub> fi<sub>n</sub>di<sub>ngs</sub> d<sub>emons</sub>t<sub>ra</sub>t<sub>e</sub> th<sub>e ex-</sub> treme im<sub>p</sub>ortance of our first <sub>g</sub>uideline in Section 5.

![](images/cbf876399c8145cb6b03d4edf60113f78a092e0238c272050ff088fc8df2109a.jpg)  
Figure 8: The efect of � in DNS(�, �), where � is set to 200, 200<sub>,</sub> 500 for Gowalla<sub>,</sub> Yel<sub>p</sub> and Amazon res<sub>p</sub>ectivel<sub>y</sub>.

## 6.4 (RQ2) Performance with Diferent S<sub>a</sub>m<sub>p</sub>lin<sub>g</sub> Di<sub>s</sub>trib<sub>u</sub>ti<sub>o</sub>n<sub>s</sub>

This s<sub>u</sub>bsection in<sub>v</sub>esti<sub>g</sub>ates ho<sub>w</sub> To<sub>p</sub>-� metrics <sub>w</sub>ill chan<sub>g</sub>e <sub>u</sub>nd<sub>er</sub> dif<sub>eren</sub>t <sub>samp</sub>li<sub>ng</sub> di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>ons on rea</sub>l<sub>-wor</sub>ld d<sub>a</sub>t<sub>ase</sub>t<sub>s.</sub> A<sub>s</sub> th<sub>e</sub> sam<sub>p</sub>lin<sub>g</sub> distribution is afected b<sub>y</sub> h<sub>yp</sub>er<sub>p</sub>arameters<sub>,</sub> see Section 5<sub>,</sub> we investi<sub>g</sub>ate the <sub>p</sub>erformance under diferent h<sub>yp</sub>er<sub>p</sub>arameter sett<sup>i</sup>n<sub>g</sub>s.

W<sub>e repor</sub>t th<sub>e per</sub>f<sub>ormance resu</sub>lt<sub>s on</sub> th<sub>ree pu</sub>bli<sub>c</sub> d<sub>a</sub>t<sub>ase</sub>t <sub>un</sub>d<sub>er</sub> diferent � in DNS(M,N), diferent N in DNS(M, N) and diferent $\rho$ in Softmax-v(<sub>�</sub>,N) in Fi<sub>g</sub>ure 8, Fi<sub>g</sub>ure 9 and Fi<sub>g</sub>ure 10 res<sub>p</sub>ectivel<sub>y</sub>. We onl<sub>y</sub> care about the relative ma<sub>g</sub>nitude of To<sub>p</sub>-� metrics<sub>,</sub> so <sub>we</sub> <sub>repor</sub>t th<sub>e</sub> <sub>re</sub>l<sub>a</sub>ti<sub>ve</sub> <sub>va</sub>l<sub>ue</sub> <sub>o</sub>f T<sub>op-</sub>� <sub>eva</sub>l<sub>ua</sub>ti<sub>on</sub> <sub>me</sub>t<sub>r</sub>i<sub>cs</sub> f<sub>or</sub> b<sub>e</sub>tt<sub>er</sub> visualization. We hi<sub>g</sub>hli<sub>g</sub>ht the value of h<sub>yp</sub>er<sub>p</sub>arameters when <sub>eac</sub>h <sub>curve reac</sub>h<sub>es</sub> it<sub>s max</sub>i<sub>mum resu</sub>lt<sub>.</sub> F<sub>or eac</sub>h <sub>resu</sub>lt<sub>, we</sub> t<sub>une</sub> the learning rate ∈ {0.01, 0.001} and weight\_decay ∈ {0.01, 0.001, 0.0001} to find the best.

![](images/04d4e3a73ef9a1bff23315006e68ce06910eb77f68b70feb6f85e72b9af21de9.jpg)

Figure 9: The efect of � in DNS(�, �), where � is set to 5 f<sub>or a</sub>ll th<sub>ree</sub> d<sub>a</sub>t<sub>ase</sub>t<sub>s.</sub>  
![](images/5165bcb0df0ec703ef220577205d31de879de45842e7ce0867dd847032b55a84.jpg)  
Figure 10: The efect of <sub>�</sub> in Softmax-v(<sub>�</sub>, �), where � is set to 200<sub>,</sub> 200<sub>,</sub> 500 for Gowalla<sub>,</sub> Yel<sub>p</sub> and Amazon res<sub>p</sub>ectivel<sub>y</sub>.

• From Fi<sub>g</sub>ure 8, we observe that for all datasets and all metrics, the lower the � in To<sub>p</sub>-� metrics is, the smaller the � in DNS(�, �) when the curve achieves its maximum <sub>p</sub>erformance.

• From Fi<sub>g</sub>ure 9, we observe that for all datasets and all metrics, the lower the � in To<sub>p</sub>-� metrics is, the lar<sub>g</sub>er the � in DNS(�, �) when the curve achieves its maximum <sub>p</sub>erformance.

• From Fi<sub>g</sub>ure 10, we observe that for all datasets and all metrics, the lower the � in To<sub>p</sub>-� metrics is<sub>,</sub> the lar<sub>g</sub>er the <sub>�</sub> in Softmax v(<sub>�</sub>, �) when the curve achieves its maximum <sub>p</sub>erformance.

I<sub>n some cases,</sub> th<sub>e pea</sub>k <sub>o</sub>f th<sub>e</sub> T<sub>op-</sub>20 <sub>curve co</sub>i<sub>nc</sub>id<sub>es w</sub>ith th<sub>e</sub> <sub>p</sub>eak of the To<sub>p</sub>-50 c<sub>u</sub>r<sub>v</sub>e or To<sub>p</sub>-5 c<sub>u</sub>r<sub>v</sub>e. This can be attrib<sub>u</sub>ted t<sub>o</sub> th<sub>e</sub> <sub>re</sub>l<sub>a</sub>ti<sub>ve</sub>l<sub>y</sub> <sub>sma</sub>ll dif<sub>erence</sub> <sub>o</sub>f �<sub>.</sub> With <sub>a</sub> l<sub>arger</sub> dif<sub>erence</sub> <sub>o</sub>f �<sub>,</sub> for exam<sub>p</sub>le<sub>,</sub> To<sub>p</sub>-50 and To<sub>p</sub>-5<sub>,</sub> their c<sub>u</sub>r<sub>v</sub>e al<sub>w</sub>a<sub>y</sub>s matches o<sub>u</sub>r observation. We conduct further ex<sub>p</sub>eriments to investi<sub>g</sub>ate the <sub>p</sub>erformance across a wide ran<sub>g</sub>e of � in A<sub>pp</sub>endix D.

Recall that we have observed how h<sub>yp</sub>er<sub>p</sub>arameters (�, �, <sub>�</sub>) afect sam<sub>p</sub>lin<sub>g</sub> hardness in Fi<sub>g</sub>ure 7. Combinin<sub>g</sub> these two obser <sub>va</sub>ti<sub>ons,</sub> <sub>we</sub> <sub>can</sub> <sub>eas</sub>il<sub>y</sub> <sub>conc</sub>l<sub>u</sub>d<sub>e</sub> th<sub>a</sub>t th<sub>e</sub> <sub>sma</sub>ll<sub>er</sub> th<sub>e</sub> � i<sub>n</sub> T<sub>op-</sub> � <sub>me</sub>t<sub>r</sub>i<sub>cs,</sub> th<sub>e</sub> h<sub>ar</sub>d<sub>er</sub> th<sub>e nega</sub>ti<sub>ve samp</sub>l<sub>es we s</sub>h<sub>ou</sub>ld d<sub>raw.</sub> Th<sub>ese c</sub>l<sub>ear</sub>l<sub>y ver</sub>if<sub>y our secon</sub>d <sub>gu</sub>id<sub>e</sub>li<sub>ne.</sub>

## 7 RELATED WORK

## 7.1 Ne<sub>g</sub>ative Sam<sub>p</sub>lin<sub>g</sub> for Recommendation

E<sub>ar</sub>l<sub>y</sub> <sub>wor</sub>k <sub>samp</sub>l<sub>e</sub> it<sub>ems</sub> b<sub>ase</sub>d <sub>on</sub> <sub>pre</sub>d<sub>e</sub>fi<sub>ne</sub>d di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>ons,</sub> <sub>e.g.,</sub> <sub>un</sub>i<sub>-</sub> form distribution [11, 29] and <sub>p</sub>o<sub>p</sub>ularit<sub>y</sub>-based distribution [3, 10]. Th<sub>ese s</sub>t<sub>a</sub>ti<sub>c samp</sub>l<sub>ers are</sub> i<sub>n</sub>d<sub>epen</sub>d<sub>en</sub>t <sub>o</sub>f <sub>mo</sub>d<sub>e</sub>l <sub>s</sub>t<sub>a</sub>t<sub>us an</sub>d <sub>un-</sub> <sub>c</sub>h<sub>ange</sub>d f<sub>or</sub> dif<sub>eren</sub>t <sub>users.</sub> Th<sub>us,</sub> th<sub>e per</sub>f<sub>ormance</sub> i<sub>s</sub> li<sub>m</sub>it<sub>e</sub>d<sub>.</sub> L<sub>a</sub>t<sub>er</sub> on, ada<sub>p</sub>tive sam<sub>p</sub>lers are <sub>p</sub>ro<sub>p</sub>osed, such as DNS [40] and softmaxb<sub>ase</sub>d <sub>samp</sub>li<sub>ng me</sub>th<sub>o</sub>d<sub>s.</sub> S<sub>o</sub>ft<sub>max-</sub>b<sub>ase</sub>d <sub>samp</sub>li<sub>ng</sub> i<sub>s w</sub>id<sub>e</sub>l<sub>y use</sub>d in adversarial learnin<sub>g</sub> (e.<sub>g</sub>. IRGAN [33] and ADVIR [26]) and im-<sub>p</sub>ortance sam<sub>p</sub>lin<sub>g</sub> (e.<sub>g</sub>. PRIS [21] and AdaSIR [9]). The<sub>y</sub> assi<sub>g</sub>n hi<sub>g</sub>h sam<sub>p</sub>lin<sub>g</sub> <sub>p</sub>robabilit<sub>y</sub> to to<sub>p</sub>-ranked ne<sub>g</sub>ative items<sub>,</sub> accounti<sub>ng</sub> f<sub>or</sub> <sub>mo</sub>d<sub>e</sub>l <sub>s</sub>t<sub>a</sub>t<sub>us.</sub> Th<sub>ere</sub> <sub>are</sub> <sub>a</sub>l<sub>so</sub> <sub>some</sub> fi<sub>ne-gra</sub>i<sub>ne</sub>d <sub>nega</sub>ti<sub>ve</sub> sam<sub>p</sub>lin<sub>g</sub> methods [23, 32, 34, 42]. Em<sub>p</sub>irical ex<sub>p</sub>eriments verif<sub>y</sub> th<sub>e e</sub>f<sub>ec</sub>ti<sub>veness an</sub>d <sub>e</sub>fi<sub>c</sub>i<sub>ency o</sub>f HNS<sub>.</sub> Th<sub>e e</sub>fi<sub>c</sub>i<sub>ency pro</sub>bl<sub>em</sub> h<sub>as</sub> been studied in AOBPR [28]. The<sub>y</sub> ar<sub>g</sub>ue that HNS sam<sub>p</sub>les more i<sub>n</sub>f<sub>orma</sub>ti<sub>ve</sub> hi<sub>g</sub>h<sub>-score</sub>d it<sub>ems, w</sub>hi<sub>c</sub>h <sub>can con</sub>t<sub>r</sub>ib<sub>u</sub>t<sub>e more</sub> t<sub>o</sub> th<sub>e</sub> <sub>gra</sub>di<sub>en</sub>t<sub>s an</sub>d <sub>acce</sub>l<sub>era</sub>t<sub>e</sub> th<sub>e convergence.</sub> N<sub>ever</sub>th<sub>e</sub>l<sub>ess,</sub> th<sub>e reasons</sub> f<sub>or</sub> th<sub>e</sub> <sub>e</sub>f<sub>ec</sub>ti<sub>veness</sub> <sub>o</sub>f HNS <sub>are</sub> <sub>no</sub>t <sub>revea</sub>l<sub>e</sub>d <sub>ye</sub>t<sub>.</sub> T<sub>o</sub> th<sub>e</sub> b<sub>es</sub>t <sub>o</sub>f our knowled<sub>g</sub>e, onl<sub>y</sub> DNS [40] <sub>p</sub>rovides clues of the connection between HNS and To<sub>p</sub>-� metrics. But unfortunatel<sub>y,</sub> the<sub>y</sub> fail to <sub>g</sub>i<sub>ve</sub> <sub>a</sub> th<sub>eore</sub>ti<sub>ca</sub>l f<sub>oun</sub>d<sub>a</sub>ti<sub>on</sub> <sub>an</sub>d d<sub>eep</sub> <sub>ana</sub>l<sub>yses.</sub>

## 7<sub>.</sub>2 P<sub>ar</sub>ti<sub>a</sub>l AUC M<sub>ax</sub>i<sub>m</sub>i<sub>za</sub>ti<sub>on</sub>

Ear<sup>l</sup>y wor<sup>k</sup> <sup>d</sup>oes not <sup>d</sup>irect<sup>l</sup>y optimize t<sup>h</sup>e surrogate o<sup>b</sup>jective o<sup>f</sup> Partia<sup>l</sup> AUC, <sup>b</sup>ut instea<sup>d</sup>, some ot<sup>h</sup>er re<sup>l</sup>ate<sup>d</sup> o<sup>b</sup>jectives, e.g., p-norm <sub>p</sub>ush [31], infinite-<sub>p</sub>ush [20], and as<sub>y</sub>mmetric SVM objective [36]. N<sub>ever</sub>th<sub>e</sub>l<sub>ess,</sub> th<sub>ese</sub> <sub>a</sub>l<sub>gor</sub>ith<sub>ms</sub> <sub>are</sub> <sub>no</sub>t <sub>sca</sub>l<sub>a</sub>bl<sub>e</sub> <sub>an</sub>d <sub>app</sub>li<sub>ca</sub>bl<sub>e</sub> t<sub>o</sub> dee<sub>p</sub> learnin<sub>g</sub>. More recentl<sub>y</sub>, [38] considers two-wa<sub>y</sub> <sub>p</sub>artial AUC maximization and sim<sub>p</sub>lifies the o<sub>p</sub>timizin<sub>g p</sub>roblem for lar<sub>g</sub>e scale o<sub>p</sub>timization. [41] <sub>p</sub>ro<sub>p</sub>oses new formulations of Partial AUC surro<sub>g</sub>ate objectives usin<sub>g</sub> distributionall<sub>y</sub> robust o<sub>p</sub>timization (DRO). Thi<sub>s wo</sub>rk m<sub>o</sub>ti<sub>va</sub>t<sub>es ou</sub>r <sub>p</sub>r<sub>oo</sub>f <sub>o</sub>f th<sub>e co</sub>nn<sub>ec</sub>ti<sub>o</sub>n b<sub>e</sub>t<sub>wee</sub>n OPAUC and HNS. A more com<sub>p</sub>rehensive stud<sub>y</sub> of AUC can refer to [37].

## 8 CONCLUSION

In this <sub>p</sub>a<sub>p</sub>er<sub>,</sub> we reveal the theories behind HNS for recommendation. We <sub>p</sub>rove that the BPR loss e<sub>q</sub>ui<sub>pp</sub>ed with HNS strate<sub>g</sub>ies <sub>op</sub>timiz<sub>es</sub> OPAUC<sub>.</sub> M<sub>ea</sub>n<sub>w</sub>hil<sub>e, we co</sub>nd<sub>uc</sub>t th<sub>eo</sub>r<sub>e</sub>ti<sub>ca</sub>l <sub>a</sub>n<sub>a</sub>l<sub>ys</sub>i<sub>s a</sub>nd simulation ex<sub>p</sub>eriments to show the stron<sub>g</sub> connection between OPAUC <sub>a</sub>nd T<sub>op</sub>-� <sub>eva</sub>l<sub>ua</sub>ti<sub>o</sub>n m<sub>e</sub>tri<sub>cs.</sub> On th<sub>ese</sub> b<sub>ases,</sub> th<sub>e e</sub>f<sub>ec</sub>- ti<sub>veness</sub> <sub>o</sub>f HNS <sub>can</sub> b<sub>e</sub> <sub>c</sub>l<sub>ear</sub>l<sub>y</sub> <sub>exp</sub>l<sub>a</sub>i<sub>ne</sub>d<sub>.</sub> T<sub>o</sub> t<sub>a</sub>k<sub>e</sub> <sub>a</sub> <sub>s</sub>t<sub>ep</sub> f<sub>ur</sub>th<sub>er,</sub> we <sub>p</sub>ro<sub>p</sub>ose two insi<sub>g</sub>htful <sub>g</sub>uidelines for efective usa<sub>g</sub>e of HNS. In conclusion<sub>,</sub> the <sub>p</sub>ro<sub>p</sub>osed theoretical understandin<sub>g</sub> of HNS can not <sub>on</sub>l<sub>y</sub> <sub>exp</sub>l<sub>a</sub>i<sub>n</sub> <sub>e</sub>f<sub>ec</sub>ti<sub>veness</sub> b<sub>u</sub>t <sub>a</sub>l<sub>so</sub> <sub>prov</sub>id<sub>e</sub> i<sub>ns</sub>i<sub>g</sub>htf<sub>u</sub>l <sub>gu</sub>id<sub>e</sub>li<sub>nes</sub> f<sub>or</sub> f<sub>u</sub>t<sub>ure</sub> <sub>s</sub>t<sub>u</sub>d<sub>y.</sub>

In the future<sub>,</sub> we will investi<sub>g</sub>ate the connection between Two-<sub>w</sub>a<sub>y</sub> Partial AUC and recommendation al<sub>g</sub>orithms<sub>,</sub> <sub>w</sub>hich ma<sub>y</sub> brin<sub>g</sub> <sub>more</sub> i<sub>ns</sub>i<sub>g</sub>ht<sub>s</sub> i<sub>n</sub>t<sub>o recommen</sub>d<sub>a</sub>ti<sub>on sys</sub>t<sub>ems.</sub> Th<sub>e e</sub>f<sub>ec</sub>t <sub>o</sub>f f<sub>a</sub>l<sub>se</sub> ne<sub>g</sub>ative items will also be an excitin<sub>g</sub> research direction.

## ACKNOWLEDGMENTS

This work is su<sub>pp</sub>orted b<sub>y</sub> the National Ke<sub>y</sub> Research and Develo<sub>p</sub>- ment Pro<sub>g</sub>ram of China (2022YFB3104701), the Starr<sub>y</sub> Ni<sub>g</sub>ht Science

Fun<sup>d</sup> o<sup>f</sup> Z<sup>h</sup>ejiang University S<sup>h</sup>ang<sup>h</sup>ai Institute <sup>f</sup>or A<sup>d</sup>vance<sup>d</sup> Stu<sup>d</sup>y (SN-ZJU-SIAS-001), the National Natural Science Foundation of China (61972372, 62121002, 62102382), and the CCCD Ke<sub>y</sub> Lab of Mini<sub>s</sub>tr<sub>y o</sub>f C<sub>u</sub>lt<sub>u</sub>r<sub>e a</sub>nd T<sub>ou</sub>ri<sub>s</sub>m<sub>.</sub>

## REFERENCES

[1] Immanuel Ba<sub>y</sub>er, Xian<sub>g</sub>nan He, Bhar<sub>g</sub>av Kana<sub>g</sub>al, and Stefen Rendle. 2017. A G<sub>e</sub>n<sub>e</sub>ri<sub>c</sub> C<sub>oo</sub>rdin<sub>a</sub>t<sub>e</sub> D<sub>esce</sub>nt Fr<sub>a</sub>m<sub>ewo</sub>rk f<sub>o</sub>r L<sub>ea</sub>rnin<sub>g</sub> fr<sub>o</sub>m Im<sub>p</sub>li<sub>c</sub>it F<sub>ee</sub>db<sub>ac</sub>k<sub>.</sub> In WWW. ACM 1341–1350.

[2] Gu<sub>y</sub> Blanc and Stefen Rendle. 2018. Ada<sub>p</sub>tive Sam<sub>p</sub>led Softmax with Kerne Based Sampling. In ICML. 590–599.

[3] Hu<sub>g</sub>o Caselles-Du<sub>p</sub>ré, Florian Lesaint, and Jimena Ro<sub>y</sub>o-Letelier. 2018. Word2vec applied to recommendation: hyperparameters matter. In RecSys. 352–356.

[4] Chon<sub>g</sub> Chen, Weizhi Ma, Min Zhan<sub>g</sub>, Chen<sub>y</sub>an<sub>g</sub> Wan<sub>g</sub>, Yi<sub>q</sub>un Liu, and Shao<sub>p</sub>in<sub>g</sub> M<sub>a.</sub> 2022<sub>.</sub> R<sub>ev</sub>i<sub>s</sub>itin<sub>g</sub> N<sub>ega</sub>ti<sub>ve</sub> S<sub>a</sub>m<sub>p</sub>lin<sub>g</sub> VS<sub>.</sub> N<sub>o</sub>n-S<sub>a</sub>m<sub>p</sub>lin<sub>g</sub> in Im<sub>p</sub>li<sub>c</sub>it R<sub>eco</sub>m mendation. ACM Trans. Inf. Syst. (2022)

[5] Chon<sub>g</sub> Chen, Min Zhan<sub>g</sub>, Weizhi Ma, Yon<sub>g</sub>fen<sub>g</sub> Zhan<sub>g</sub>, Yi<sub>q</sub>un Liu, and Shao<sub>p</sub>in<sub>g</sub> M<sub>a.</sub> 2020<sub>.</sub> Efi<sub>c</sub>i<sub>e</sub>nt H<sub>e</sub>t<sub>e</sub>r<sub>oge</sub>n<sub>eous</sub> C<sub>o</sub>ll<sub>a</sub>b<sub>o</sub>r<sub>a</sub>ti<sub>ve</sub> Filt<sub>e</sub>rin<sub>g w</sub>ith<sub>ou</sub>t N<sub>ega</sub>ti<sub>ve</sub> Sampling for Recommendation. In AAAI.

[6] Chon<sub>g</sub> Chen, Min Zhan<sub>g</sub>, Yon<sub>g</sub>fen<sub>g</sub> Zhan<sub>g</sub>, Yi<sub>q</sub>un Liu, and Shao<sub>p</sub>in<sub>g</sub> Ma. 2020. Efi<sub>c</sub>i<sub>e</sub>nt N<sub>eu</sub>r<sub>a</sub>l M<sub>a</sub>trix F<sub>ac</sub>t<sub>o</sub>riz<sub>a</sub>ti<sub>o</sub>n <sub>w</sub>ith<sub>ou</sub>t S<sub>a</sub>m<sub>p</sub>lin<sub>g</sub> f<sub>o</sub>r R<sub>eco</sub>mm<sub>e</sub>nd<sub>a</sub>ti<sub>o</sub>n<sub>.</sub> ACM Trans. Inf. Syst. 38 (2020).

[7] Jiawei Chen, Hande Don<sub>g</sub>, Xian<sub>g</sub> Wan<sub>g</sub>, Fuli Fen<sub>g</sub>, Men<sub>g</sub> Wan<sub>g</sub>, and Xian<sub>g</sub>nan He. 2020<sub>.</sub> Bi<sub>as a</sub>nd D<sub>e</sub>bi<sub>as</sub> in R<sub>eco</sub>mm<sub>e</sub>nd<sub>e</sub>r S<sub>ys</sub>t<sub>e</sub>m: A S<sub>u</sub>r<sub>vey a</sub>nd F<sub>u</sub>t<sub>u</sub>r<sub>e</sub> Dir<sub>ec</sub>ti<sub>o</sub>n<sub>s.</sub> CoRR abs/2010.03240 (2020).

[8] Jiawei Chen, Chen<sub>gq</sub>uan Jian<sub>g</sub>, Can Wan<sub>g</sub>, Shen<sub>g</sub> Zhou, Yan Fen<sub>g</sub>, Chun Chen, M<sub>a</sub>rtin E<sub>s</sub>t<sub>e</sub>r<sub>, a</sub>nd Xi<sub>a</sub>n n<sub>a</sub>n H<sub>e.</sub> 2021<sub>.</sub> C<sub>o</sub>S<sub>a</sub>m: An Efi<sub>c</sub>i<sub>e</sub>nt C<sub>o</sub>ll<sub>a</sub>b<sub>o</sub>r<sub>a</sub>ti<sub>ve</sub> Ad<sub>a</sub> ti<sub>ve</sub> Sampler for Recommendation. ACM Trans. Inf. Syst. 39 (2021).

[9] Jin Chen, Defu Lian, Binbin Jin, Kai Zhen<sub>g</sub>, and Enhon<sub>g</sub> Chen. 2022. Learnin<sub>g</sub> Recommenders for Implicit Feedback with Importance Resampling. In WWW. 1997–2005.

[10] Tin<sub>g</sub> Chen, Yizhou Sun, Yue Shi, and Lian<sub>g</sub>jie Hon<sub>g</sub>. 2017. On Sam<sub>p</sub>lin<sub>g</sub> Strate<sub>g</sub>ies for Neural Network-based Collaborative Filtering. In SIGKDD.

[11] Jingtao Ding, Yuhan Quan, Xiangnan He, Yong Li, and Depeng Jin. 2019. Rein forced Negative Sampling for Recommendation with Exposure Data. In IJCAI. 2230–2236.

[12] Jingtao Ding, Yuhan Quan, Quanming Yao, Yong Li, and Depeng Jin. 2020. Simplify and Robustify Negative Sampling for Implicit Collaborative Filtering. In NIPS. 1094–1105.

[13] Lori E Dodd and Mar<sub>g</sub>aret S Pe<sub>p</sub>e. 2003. Partial AUC estimation and re<sub>g</sub>ression. Biometrics 59, 3 (2003), 614–623.

[14] John C. Duchi and Hon<sub>g</sub>seok Namkoon<sub>g</sub>. 2018. Learnin<sub>g</sub> Models with Uniform Performance via Distributionally Robust Optimization. CoRR abs/1810.08750 (2018).

[15] Louis Faur<sub>y</sub>, U<sub>g</sub>o Tanielian, Elvis Dohmatob, Elena Smirnova, and Flavian Vasile. 2020. Distributionally Robust Counterfactual Risk Minimization. In AAAI. 3850– 3857.

[16] Wei Gao and Zhi-Hua Zhou. 2015. On the Consistenc<sub>y</sub> of AUC Pairwise O<sub>p</sub>ti mization. In IJCAI. 939–945.

[17] Xian<sub>g</sub>nan He, Hanwan<sub>g</sub> Zhan<sub>g</sub>, Min-Yen Kan, and Tat-Sen<sub>g</sub> Chua. 2016. Fast M<sub>a</sub>trix F<sub>ac</sub>t<sub>o</sub>riz<sub>a</sub>ti<sub>o</sub>n f<sub>o</sub>r Onlin<sub>e</sub> R<sub>eco</sub>mm<sub>e</sub>nd<sub>a</sub>ti<sub>o</sub>n <sub>w</sub>ith Im<sub>p</sub>li<sub>c</sub>it F<sub>ee</sub>db<sub>ac</sub>k<sub>.</sub> In SIGIR. ACM, 549–558.

[18] Zhaolin Hu and L Jef Hon<sub>g</sub>. 2013. Kullback-Leibler diver<sub>g</sub>ence constrained distributionally robust optimization. Available at Optimization Online (2013), 1695–1724.

[19] Daniel Lev<sub>y</sub>, Yair Carmon, John C Duchi, and Aaron Sidford. 2020. Lar<sub>g</sub>e-Scale Methods for Distributionall Robust O timization. In NIPS, Vol. 33. 8847–8860.

[20] Nan Li, Ron Jin, and Zhi-Hua Zhou. 2014. To Rank O timization in Linear Time. In NIPS. 1502–1510.

[21] Defu Lian, Qi Liu, and Enhon<sub>g</sub> Chen. 2020. Personalized Rankin<sub>g</sub> with Im<sub>p</sub>ortance Sampling. In WWW. 1093–1103.

[22] Fen<sub>g</sub>min<sub>g</sub> Lin, Xiaolei Fan<sub>g</sub>, and Zhemin<sub>g</sub> Gao. 2022. Distributionall<sub>y</sub> Robust Optimization: A review on theory and applications. Numerical Algebra, Control and Optimization 12 (2022), 159–212.

[23] Xin Mao, Wentin<sub>g</sub> Wan<sub>g</sub>, Yuanbin Wu, and Man Lan. 2021. Boostin<sub>g</sub> the S<sub>p</sub>eed <sub>o</sub>f Entit<sub>y</sub> Ali<sub>g</sub>nm<sub>e</sub>nt 10 ×: D<sub>ua</sub>l Att<sub>e</sub>nti<sub>o</sub>n M<sub>a</sub>t<sub>c</sub>hin<sub>g</sub> N<sub>e</sub>t<sub>wo</sub>rk <sub>w</sub>ith N<sub>o</sub>rm<sub>a</sub>liz<sub>e</sub>d Hard Sample Mining. In WWW. 821–832.

[24] Donna McClish. 1989. Analyzing a portion of the ROC Curve. Medical decision making : an international journal ofthe Society for Medical Decision Making 9 (1989), 190–5.

[25] Khasha<sub>y</sub>ar Namdar, Masoom A. Haider, and Farzad Khalvati. 2021. A Modi fi<sub>e</sub>d AUC f<sub>or</sub> T<sub>ra</sub>i<sub>n</sub>i<sub>n</sub> C<sub>onvo</sub>l<sub>u</sub>ti<sub>ona</sub>l N<sub>eura</sub>l N<sub>e</sub>t<sub>wor</sub>k<sub>s:</sub> T<sub>a</sub>ki<sub>n</sub> C<sub>on</sub>fid<sub>ence</sub> I<sub>n</sub>t<sub>o</sub> Account. Frontiers Artif. Intell. 4 (2021), 582928.

[26] Dae Hoon Park and Yi Chan<sub>g</sub>. 2019. Adversarial Sam<sub>p</sub>lin<sub>g</sub> and Trainin<sub>g</sub> for Semi-Su ervised Information Retrieval. In WWW. 1443–1453.

[27] Hamed Rahimian and Sanja<sub>y</sub> Mehrotra. 2019. Distributionall<sub>y</sub> Robust O<sub>p</sub>timiza tion: A Review. CoRR abs/1908.05659 (2019).

[28] Stefen Rendle and Christo<sub>p</sub>h Freudenthaler. 2014. Im<sub>p</sub>rovin<sub>g</sub> Pairwise Learnin<sub>g</sub> for Item Recommendation from Implicit Feedback. In WSDM. 273–282.

[29] Stefen Rendle, Christo<sub>p</sub>h Freudenthaler, Zeno Gantner, and Lars Schmidt-Thieme. 2009. BPR: Bayesian Personalized Ranking from Implicit Feedback. In UAI. 452– 461.

[30] R T<sub>y</sub>rrell Rockafellar. 2017. Risk and utilit<sub>y</sub> in the dualit<sub>y</sub> framework of convex analysis. In Jonathan M. Borwein Commemorative Conference. 21–42.

[31] C<sub>y</sub>nthia Rudin. 2009. The P-Norm Push: A Sim<sub>p</sub>le Convex Rankin<sub>g</sub> Al<sub>g</sub>orithm That Concentrates at the Top ofthe List. J. Mach. Learn. Res. 10 (2009), 2233–2271.

[32] Qi Wan, Xian<sub>g</sub>nan He, Xian<sub>g</sub> Wan<sub>g</sub>, Jiancan Wu, Wei Guo, and Ruimin<sub>g</sub> Tan<sub>g</sub>. 2022. Cross Pairwise Ranking for Unbiased Item Recommendation. In WWW. 2370–2378.

[33] Jun Wan<sub>g</sub>, Lantao Yu, Weinan Zhan<sub>g</sub>, Yu Gon<sub>g</sub>, Yin<sub>g</sub>hui Xu, Ben<sub>y</sub>ou Wan<sub>g</sub>, Pen<sub>g</sub> Zh<sub>a</sub>n<sub>g, a</sub>nd D<sub>e</sub>ll Zh<sub>a</sub>n<sub>g.</sub> 2017<sub>.</sub> IRGAN: A Minim<sub>a</sub>x G<sub>a</sub>m<sub>e</sub> f<sub>o</sub>r Unif<sub>y</sub>in<sub>g</sub> G<sub>e</sub>n<sub>e</sub>r<sub>a</sub>ti<sub>ve</sub> and Discriminative Information Retrieval Models. In SIGIR. 515–524

[34] Xian<sub>g</sub> Wan<sub>g</sub>, Yaokun Xu, Xian<sub>g</sub>nan He, Yixin Cao, Men<sub>g</sub> Wan<sub>g</sub>, and Tat-Sen<sub>g</sub> Chua. 2020. Reinforced Ne<sub>g</sub>ative Sam<sub>p</sub>lin<sub>g</sub> over Knowled<sub>g</sub>e Gra<sub>p</sub>h for Recom mendation. In WWW. 99–109.

[35] Jason Weston, Sam<sub>y</sub> Ben<sub>g</sub>io, and Nicolas Usunier. 2011. WSABIE: Scalin<sub>g</sub> u<sub>p</sub> to Lar e Vocabular Ima e Annotation. In IJCAI. 2764–2770.

[36] Shan-Hun<sub>g</sub> Wu, Ken<sub>g</sub>-Pei Lin, Chun<sub>g</sub>-Min Chen, and Min<sub>g</sub>-S<sub>y</sub>an Chen. 2008. As<sub>y</sub>mmetric su<sub>pp</sub>ort vector machines: low false-<sub>p</sub>ositive learnin<sub>g</sub> under the user tolerance. In KDD. ACM, 749–757.

[37] Tianbao Yan<sub>g</sub> and Yimin<sub>g</sub> Yin<sub>g</sub>. 2022. AUC Maximization in the Era of Bi<sub>g</sub> Data and AI: A Survey. ACM Comput. Surv. (jul 2022).

[38] Zhiyong Yang, Qianqian Xu, Shilong Bao, Yuan He, Xiaochun Cao, and Qingming H<sub>ua</sub>n<sub>g.</sub> 2021<sub>.</sub> Wh<sub>e</sub>n All W<sub>e</sub> N<sub>ee</sub>d i<sub>s a</sub> Pi<sub>ece o</sub>f th<sub>e</sub> Pi<sub>e</sub>: A G<sub>e</sub>n<sub>e</sub>ri<sub>c</sub> Fr<sub>a</sub>m<sub>ewo</sub>rk f<sub>o</sub>r Optimizing Two-way Partial AUC. In ICML. 11820–11829.

[39] Runtian Zhai, Chen Dan, J. Zico Kolter, and Pradee<sub>p</sub> Ravikumar. 2021. DORO: Distributional and Outlier Robust Optimization. In ICML. 12345–12355.

[40] Weinan Zhan<sub>g</sub>, Tian<sub>q</sub>i Chen, Jun Wan<sub>g</sub>, and Yon<sub>g</sub> Yu. 2013. O<sub>p</sub>timizin<sub>g</sub> to<sub>p</sub>-n collaborative filtering via dynamic negative item sampling. In SIGIR. 785–788.

[41] Dixian Zhu, Gan<sub>g</sub> Li, Bokun Wan<sub>g</sub>, Xiaodon<sub>g</sub> Wu, and Tianbao Yan<sub>g</sub>. 2022. When AUC m<sub>ee</sub>t<sub>s</sub> DRO: O<sub>p</sub>timizin<sub>g</sub> P<sub>a</sub>rti<sub>a</sub>l AUC f<sub>o</sub>r D<sub>eep</sub> L<sub>ea</sub>rnin<sub>g w</sub>ith N<sub>o</sub>n-C<sub>o</sub>n<sub>ve</sub>x Conver ence Guarantee. In ICML. 27548–27573

[42] Qiannan Zhu, Haobo Zhang, Qing He, and Zhicheng Dou. 2022. A Gain-Tuning Dynamic Negative Sampler for Recommendation. In WWW. 277–285.

## A PROOF OF THEOREM 2

Proof. As shown in Lemma 1, the DRO-based objective (E<sub>q</sub>. (13)) is e<sub>q</sub>uivalent to OPAUC(�) (E<sub>q</sub>. (9)). B<sub>y</sub> re<sub>p</sub>lacin<sub>g</sub> CVaR diver<sub>g</sub>ence <sub>w</sub>ith KL di<sub>ve</sub>r<sub>ge</sub>n<sub>ce</sub> $\begin{array} { r } { D _ { \phi } = D _ { K L } ( Q | | P _ { 0 } ) = \int \log ( \frac { \mathrm { d } Q } { \mathrm { d } P } ) \mathrm { d } Q } \end{array}$ <sub>,</sub> th<sub>en</sub> th<sub>e</sub> DRO-based objective (E<sub>q</sub>. (13))) reduces to

$$
\min _ {\theta} \min _ {\lambda \geq 0} \frac {1}{| C |} \sum_ {c \in C} \frac {1}{n _ {+}} \sum_ {i \in L _ {c} ^ {+}} \left\{\lambda_ {i} \cdot \log E _ {j \sim P _ {0}} \left[ \exp \left(\frac {L (c , i , j)}{\lambda_ {i}}\right) \right] + \lambda_ {i} \cdot \rho \right\}.\tag{21}
$$

The detailed derivation can be found in [18]. B<sub>y</sub> settin<sub>g</sub> $\beta = \exp ( - \rho )$ we get a surrogate o<sup>b</sup>jective o<sup>f</sup> $O P A U C ( \beta )$ <sub>.</sub> N<sub>ex</sub>t<sub>, we w</sub>ill <sub>s</sub>h<sub>ow</sub> th<sub>a</sub>t it i<sub>s equ</sub>i<sub>va</sub>l<sub>en</sub>t t<sub>o</sub> th<sub>e so</sub>ft<sub>max-</sub>b<sub>ase</sub>d <sub>samp</sub>li<sub>ng pro</sub>bl<sub>em.</sub>

Di<sup>f</sup>erentiate t<sup>h</sup>e o<sup>b</sup>jective respect to $\lambda _ { i }$ <sub>an</sub>d <sub>se</sub>t t<sub>o</sub> 0<sub>, an</sub>d th<sub>en we</sub> fi<sub>n</sub>d th<sub>a</sub>t th<sub>e op</sub>ti<sub>ma</sub>l $\lambda _ { i }$ i<sub>s</sub> th<sub>e so</sub>l<sub>u</sub>ti<sub>on</sub> t<sub>o</sub> th<sub>e</sub> fi<sub>xe</sub>d<sub>-po</sub>i<sub>n</sub>t <sub>equa</sub>ti<sub>on:</sub>

$$
\lambda_ {i} = E _ {j \sim P _ {0}} \left[ \frac {e ^ {\frac {L (c , i , j)}{\lambda_ {i}}} \cdot L (c , i , j)}{E _ {j \sim P _ {0}} \left[ e ^ {\frac {L (c , i , j)}{\lambda_ {i}}} \right]} \right] \cdot \frac {1}{\rho + \log E _ {j \sim P _ {0}} \left[ e ^ {\frac {L (c , i , j)}{\lambda_ {i}}} \right]}.\tag{22}
$$

R<sub>ep</sub>l<sub>ace</sub> th<sub>e a</sub>b<sub>ove va</sub>l<sub>ue</sub> f<sub>or</sub> $\lambda _ { i }$ in E<sub>q</sub>. (21), and then we derive the f<sub>o</sub>ll<sub>ow</sub>i<sub>ng resu</sub>lt<sub>:</sub>

$$
\min _ {\theta} \frac {1}{| C |} \sum_ {c \in C} \frac {1}{n _ {+}} \sum_ {i \in \mathcal {I} _ {c} ^ {+}} \{E _ {j \sim P _ {0}} \left[ \frac {e ^ {\frac {L (c , i , j)}{\lambda_ {i}}}}{E _ {j \sim P _ {0}} \left[ e ^ {\frac {L (c , i , j)}{\lambda_ {i}}} \right]} L (c, i, j) \right] \},\tag{23}
$$

<sub>w</sub>h<sub>ere</sub> $P _ { 0 }$ d<sub>eno</sub>t<sub>es un</sub>if<sub>orm</sub> di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on over</sub> $\varPsi _ { c } ^ { - }$ . <sup>B</sup><sub>y</sub> sett<sup>i</sup>n<sub>g</sub> $\lambda _ { i } = \tau ,$ the analo<sub>gy</sub> of E<sub>q</sub>. (23) and the softmax sam<sub>p</sub>lin<sub>g</sub> based <sub>p</sub>roblem $( \operatorname { E q . } \left( 1 \right) )$ i<sub>s o</sub>b<sub>v</sub>i<sub>ous.</sub> Th<sub>e on</sub>l<sub>y</sub> dif<sub>erence</sub> i<sub>s</sub> th<sub>a</sub>t th<sub>e</sub> i<sub>n</sub>d<sub>ex</sub> t<sub>erm</sub> i<sub>n</sub> E<sub>q</sub>. (23) is $\frac { \ell ( r _ { c i } - r _ { c j } ) } { \tau }$ b<sub>u</sub>t $\frac { r _ { c j } - r _ { c i } } { \tau }$ in $\operatorname { E q . } \left( 1 \right)$ . When choosin<sub>g</sub> $\ell ( t ) =$ lo<sub>g</sub>(1 + ex<sub>p</sub>(−�)), it is consistent for o<sub>p</sub>timization.

B<sub>y now, we</sub> h<sub>ave proven</sub> th<sub>e equ</sub>i<sub>va</sub>l<sub>ence</sub> b<sub>e</sub>t<sub>ween so</sub>ft<sub>max sam-</sub> <sub>p</sub>li<sub>ng</sub> b<sub>ase</sub>d <sub>pro</sub>bl<sub>em</sub> $( \mathrm { E q . } ( 1 ) )$ ) and $\operatorname { O P A U C } ( \beta )$ objective (E<sub>q</sub>. (9)). How ever<sub>,</sub> it is im<sub>p</sub>ossible to directl<sub>y</sub> com<sub>p</sub>ute $\lambda _ { i }$ with E<sub>q</sub>. (22). Hence, followin<sub>g</sub> [15], we <sub>p</sub>ro<sub>p</sub>ose a<sub>pp</sub>roximation of o<sub>p</sub>timal tem<sub>p</sub>erature p<sup>arameter</sup> $\lambda _ { i } . \mathrm { A }$ second-order Ta<sub>y</sub>lor ex<sub>p</sub>ansion around 0 of E<sub>q</sub>. (21) <sub>y</sub>i<sub>e</sub>ld<sub>:</sub>

$$
\begin{array}{c} \min _ {\theta} \min _ {\lambda \geq 0} \frac {1}{| C |} \sum_ {c \in C} \frac {1}{n _ {+}} \sum_ {i \in \mathcal {I} _ {c} ^ {+}} \{\lambda_ {i} \cdot \rho + E _ {j \sim P _ {0}} [ L (c, i, j) ] + \\ \frac {\operatorname{Var} _ {j} (L (c , i , j))}{2 \lambda_ {i}} + o _ {\infty} (\frac {1}{\lambda_ {i}}) \}, \end{array}\tag{24}
$$

<sub>w</sub>h<sub>ere</sub> $\mathrm { V a r } _ { j } ( L ( c , i , j ) )$ is defined in E<sub>q</sub>. (18). Solvin<sub>g</sub> the above e<sub>q</sub>uation <sub>y</sub>ields a<sub>pp</sub>roximated o<sub>p</sub>timal tem<sub>p</sub>erature <sub>p</sub>arameter $\lambda _ { i } { \mathrm { : } }$

$$
\lambda_ {i} \simeq \sqrt {\frac {\mathrm{Var} _ {j} (L (c , i , j))}{2 \rho}} = \sqrt {\frac {\mathrm{Var} _ {j} (L (c , i , j))}{- 2 \log \beta}}.\tag{25}
$$

□

## B PROOF OF THEOREM 3

Proof. S<sub>upp</sub>ose there are $i ( i < K )$ <sub>pos</sub>iti<sub>ve</sub> it<sub>e</sub>m<sub>s</sub> in T<sub>op</sub>-� it<sub>e</sub>m<sub>s</sub> of the <sub>p</sub>ermutation, and then we have ������@� = �/�. Under this <sub>con</sub>diti<sub>on, eas</sub>il<sub>y, we can</sub> fi<sub>n</sub>d <sub>ou</sub>t th<sub>e case w</sub>hi<sub>c</sub>h h<sub>as</sub> th<sub>e max</sub>i<sub>mum</sub> value of OPAUC(�), where $\begin{array} { r } { \beta = \frac { K } { N _ { - } } } \end{array}$ :

$$
\underbrace {+ \cdots +} _ {i} \underbrace {- \cdots -} _ {K - i} | \underbrace {+ \cdots +} _ {N _ {+} - i} \underbrace {- \cdots -} _ {N _ {-} - K + i}
$$

Hence, the maximum value of OPAUC(�) is $\frac { - i ^ { 2 } + ( N _ { + } + K ) i } { N _ { + } N _ { - } }$ . Mean-<sub>w</sub>hil<sub>e, s</sub>i<sub>nce</sub> � <sub>can on</sub>l b<sub>e</sub> i<sub>n</sub>t<sub>e ers, we</sub> d<sub>er</sub>i<sub>ve</sub> th<sub>a</sub>t<sub>:</sub>

$$
\begin{array}{r l} \frac {1}{N _ {+}} \left[ \frac {N _ {+} + K - \sqrt {(N _ {+} + K) ^ {2} - 4 N _ {+} N _ {-} \times O P A U C (\beta)}}{2} \right] & \leq R e c a l l @ K. \end{array}
$$

Si<sub>m</sub>il<sub>ar</sub>l<sub>y,</sub> <sub>we</sub> <sub>can</sub> fi<sub>n</sub>d <sub>ou</sub>t th<sub>e</sub> <sub>case</sub> <sub>w</sub>hi<sub>c</sub>h h<sub>as</sub> th<sub>e</sub> <sub>m</sub>i<sub>n</sub>i<sub>mum</sub> <sub>va</sub>l<sub>ue</sub> of OPAUC(�):

$$
\underbrace {- \cdots -} _ {K - i} \underbrace {+ \cdots +} _ {i} | \underbrace {- \cdots -} _ {i} \underbrace {\cdots} _ {N _ {+} + N _ {-} - K - i}
$$

Hence, the minimum value of OPAUC(�) is $\frac { i ^ { 2 } } { N _ { + } N _ { - } }$ . Since � can onl<sub>y</sub> b<sub>e</sub> i<sub>n</sub>t<sub>egers, we can a</sub>l<sub>so</sub> d<sub>er</sub>i<sub>ve</sub> th<sub>a</sub>t<sub>:</sub>

$$
\text { Recall@K } \leq \frac {1}{N _ {+}} \left[ \sqrt {N _ {+} N _ {-} \times O P A U C (\beta)} \right].
$$

These com<sub>p</sub>lete the <sub>p</sub>roof of E<sub>q</sub>. (19). Noticin<sub>g</sub> that for a <sub>g</sub>iven <sub>p</sub>ermutation, ���������@ $\begin{array} { r } { K = \frac { N _ { + } } { K } } \end{array}$ · ������@�, where $\frac { N _ { + } } { K }$ is a constant. Hence, we can easil<sub>y</sub> derive the E<sub>q</sub>. (20). □

## C METRICS

Su<sub>pp</sub>ose we sort the left items in descendin<sub>g</sub> order accordin<sub>g</sub> to scores $r _ { c j }$ f<sub>or eac</sub>h <sub>con</sub>t<sub>ex</sub>t <sub>c.</sub> Th<sub>e pos</sub>iti<sub>ve</sub> it<sub>em se</sub>t<sub>s are</sub> d<sub>eno</sub>t<sub>e</sub>d as $\tilde { \cal J } _ { c , t e s t } ^ { + } .$ <sub>.</sub> Th<sub>e</sub> d<sub>e</sub>t<sub>a</sub>il<sub>e</sub>d d<sub>e</sub>fi<sub>n</sub>iti<sub>ons o</sub>f th<sub>e w</sub>id<sub>e</sub>l<sub>y-use</sub>d <sub>me</sub>t<sub>r</sub>i<sub>cs are</sub> <sub>summar</sub>i<sub>ze</sub>d <sub>as</sub> f<sub>o</sub>ll<sub>ow:</sub>

• Precision@�: metrics the fraction of <sub>p</sub>ositive items amon<sub>g</sub> the to<sub>p</sub> � <sub>p</sub>redicted items:

$$
P r e c i s i o n @ K = \frac {\left| \left\{j \in \mathcal {I} _ {c , t e s t} ^ {+} \mid R a n k _ {j} <   K \right\} \right|}{K}.
$$

• Recall@�: metrics the fraction of all <sub>p</sub>ositive items that were recovered in the to<sub>p</sub> K:

$$
\text { Recall@ } K = \frac {\left| \left\{j \in \mathcal {I} _ {c , t e s t} ^ {+} \mid R a n k _ {j} <   K \right\} \right|}{\left| \mathcal {I} _ {c , t e s t} ^ {+} \right|}.
$$

• NDCG@� metrics the <sub>q</sub>ualit<sub>y</sub> of recommendation throu<sub>g</sub>h discounted im<sub>p</sub>ortance based on <sub>p</sub>osition:

$$
N D C G @ K = \frac {1}{\sum_ {i = 1} ^ {\min (| \mathcal {I} _ {c , t e s t} ^ {+} | , K)} \frac {1}{\log_ {2} (i + 1)}} \sum_ {j \in \mathcal {I} _ {c, t e s t} ^ {+}} \frac {\mathbb {I} (R a n k _ {j} <   K)}{\log_ {2} (R a n k _ {j} + 1)}.
$$

## D PERFORMANCE ACROSS A WIDE RANGE OF K UNDER DIFFERENT SAMPLING DISTRIBUTION

In thi<sub>s su</sub>b<sub>sec</sub>ti<sub>o</sub>n<sub>, we</sub> in<sub>ves</sub>ti<sub>ga</sub>t<sub>e</sub> h<sub>ow</sub> T<sub>op</sub>-� m<sub>e</sub>tri<sub>cs ac</sub>r<sub>oss a w</sub>id<sub>e</sub> ran<sub>g</sub>e of � will chan<sub>g</sub>e under diferent sam<sub>p</sub>lin<sub>g</sub> distributions. For sim<sub>p</sub>licit<sub>y</sub> re<sub>p</sub>resentation<sub>,</sub> we onl<sub>y</sub> investi<sub>g</sub>ate h<sub>yp</sub>er<sub>p</sub>arameters � in DNS(�, �). As shown in Fi<sub>g</sub>ure 11, we observe that:

• The lower the � in To<sub>p</sub>-� metrics is, the lar<sub>g</sub>er the � in DNS(�, �) when the curve achieves its maximum <sub>p</sub>erformance.

• With a lar<sub>g</sub>er diference of K, there is a lar<sub>g</sub>er <sub>g</sub>a<sub>p</sub> when the curve achie<sub>v</sub>es its maxim<sub>u</sub>m <sub>p</sub>erformance.

![](images/fc1f2b857c5af1480830b83d4e7903a10f92f5de1dd4f677d942e1d0c5a01cbe.jpg)  
Figure 11: The efect of � in DNS(�, �), where � is set to 5 for all three datasets.

T<sub>a</sub>bl<sub>e</sub> 3<sub>:</sub> P<sub>er</sub>f<sub>ormance compar</sub>i<sub>son on</sub> th<sub>ree</sub> d<sub>a</sub>t<sub>ase</sub>t<sub>s us</sub>i<sub>ng</sub> Li<sub>g</sub>htGCN<sub>.</sub> Th<sub>e</sub> b<sub>es</sub>t <sub>resu</sub>lt<sub>s are</sub> i<sub>n</sub> b<sub>o</sub>ld <sub>an</sub>d th<sub>e secon</sub>d b<sub>es</sub>t <sub>are</sub> <sub>un</sub>d<sub>er</sub>li<sub>ne</sub>d<sub>.</sub>“\*\*” d<sub>eno</sub>t<sub>e</sub> th<sub>e</sub> i<sub>mprovemen</sub>t i<sub>s</sub> <sub>s</sub>i<sub>gn</sub>ifi<sub>can</sub>t <sub>w</sub>ith t<sub>-</sub>t<sub>es</sub>t <sub>w</sub>ith <sub>�</sub> < 0<sub>.</sub>05<sub>.</sub>

<table><tr><td rowspan="2">Method</td><td colspan="2">Gowalla</td><td colspan="2">Yelp</td><td colspan="2">Amazon</td></tr><tr><td>NDCG@50</td><td>Recall@50</td><td>NDCG@50</td><td>Recall@50</td><td>NDCG@50</td><td>Recall@50</td></tr><tr><td>BPR</td><td>0.1469</td><td>0.2470</td><td>0.0742</td><td>0.1507</td><td>0.0566</td><td>0.1307</td></tr><tr><td>PRIS(U)</td><td>0.1604</td><td>0.2677</td><td>0.0831</td><td>0.1670</td><td>0.0527</td><td>0.1221</td></tr><tr><td>PRIS(P)</td><td>0.1665</td><td>0.2753</td><td>0.0870</td><td>0.1741</td><td>0.0602</td><td>0.1369</td></tr><tr><td>AdaSIR(U)</td><td>0.1804</td><td>0.2979</td><td>0.0918</td><td>0.1808</td><td>0.0804</td><td>0.1719</td></tr><tr><td>AdaSIR(P)</td><td>0.1806</td><td>0.2974</td><td>0.0914</td><td>0.1796</td><td>0.0804</td><td>0.1712</td></tr><tr><td>DNS(*)</td><td> $\underline{0.1954^{**}}$ </td><td> $\underline{0.3176^{**}}$ </td><td> $\underline{0.0984^{**}}$ </td><td> $\underline{0.1926^{**}}$ </td><td> $\underline{0.1060^{**}}$ </td><td> $\underline{0.2106^{**}}$ </td></tr><tr><td>Softmax-v</td><td> $\underline{0.1991^{**}}$ </td><td> $\underline{0.3209^{**}}$ </td><td> $\underline{0.1012^{**}}$ </td><td> $\underline{0.1974^{**}}$ </td><td> $\underline{0.1100^{**}}$ </td><td> $\underline{0.2134^{**}}$ </td></tr></table>

## E ADDITIONAL EXPERIMENTS WITH LIGHTGCN

A<sub>s s</sub>h<sub>own</sub> i<sub>n</sub> T<sub>a</sub>bl<sub>e</sub> 3<sub>, we con</sub>d<sub>uc</sub>t <sub>a</sub>dditi<sub>ona</sub>l <sub>exper</sub>i<sub>men</sub>t<sub>s on</sub> th<sub>e</sub> Li<sub>g</sub>htGCN model, <sub>g</sub>ettin<sub>g</sub> similar results. Our methods DNS(�, �), Softmax-v(<sub>�</sub>, �) si<sub>g</sub>nificantl<sub>y</sub> out<sub>p</sub>erform BPR and HNS baselines, <sub>w</sub>hi<sub>c</sub>h i<sub>s co</sub>n<sub>s</sub>i<sub>s</sub>t<sub>e</sub>nt <sub>w</sub>ith <sub>ou</sub>r <sub>a</sub>n<sub>a</sub>l<sub>ys</sub>i<sub>s</sub> in S<sub>u</sub>b<sub>sec</sub>ti<sub>o</sub>n 6<sub>.</sub>3<sub>.</sub>

## F DISCUSSION

O<sub>ur ana</sub>l<sub>ys</sub>i<sub>s</sub> f<sub>or</sub> BPR l<sub>oss can</sub> b<sub>e genera</sub>li<sub>ze</sub>d t<sub>o o</sub>th<sub>er</sub> l<sub>oss</sub> f<sub>unc</sub>ti<sub>ons,</sub> like BCE loss<sub>,</sub> Tri<sub>p</sub>let loss<sub>,</sub> Softmax loss<sub>,</sub> and InfoNCE loss<sub>, w</sub>hich are widel<sub>y</sub> a<sub>pp</sub>lied in recommendation or other areas. Generall<sub>y</sub> <sub>spea</sub>kin<sub>g,</sub> th<sub>ese</sub> l<sub>oss</sub> f<sub>u</sub>n<sub>c</sub>ti<sub>o</sub>n<sub>s</sub> h<sub>ave a</sub> hi<sub>g</sub>h <sub>co</sub>rr<sub>e</sub>l<sub>a</sub>ti<sub>o</sub>n <sub>w</sub>ith th<sub>e</sub> AUC <sub>me</sub>t<sub>r</sub>i<sub>c,</sub> <sub>an</sub>d <sub>our</sub> <sub>conc</sub>l<sub>us</sub>i<sub>ons</sub> <sub>a</sub>l<sub>so</sub> <sub>wor</sub>k f<sub>or</sub> th<sub>em.</sub> Th<sub>eore</sub>ti<sub>ca</sub>ll<sub>y,</sub> <sub>we</sub> have the followin<sub>g</sub> discussions. BCE o<sub>p</sub>timizes a modified version of AUC [25]; BPR loss is a soft version of Tri<sub>p</sub>let loss. Adjustin<sub>g</sub> mar<sub>g</sub>in term in Tri<sub>p</sub>let loss is e<sub>q</sub>ual to adjustin<sub>g</sub> M in DNS(�, �); Softmax-v(<sub>�</sub>, �) is the u<sub>pp</sub>er bound of Softmax loss and InfoNCE <sup>l</sup>oss. A<sup>d</sup>justing t<sup>h</sup>e temperature in So<sup>f</sup>tmax <sup>l</sup>oss an<sup>d</sup> In<sup>f</sup>oNCE <sup>l</sup>oss is e<sub>q</sub>ual to adjustin<sub>g �</sub> in Softmax-v(<sub>�</sub>, �).