---
title: "2017-Siffer-SPOT-EVT-Anomaly-Streams"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2017-Siffer-SPOT-EVT-Anomaly-Streams.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Anomaly Detection in Streams with Extreme Value Theory

Alb<sub>an</sub> Sif<sub>er</sub> Am<sub>ossys,</sub> IRISA<sub>,</sub> Inri<sub>a</sub> <sub>a</sub>lb<sub>an.s</sub>if<sub>er@</sub>i<sub>r</sub>i<sub>sa.</sub>f<sub>r</sub>

Al<sub>exan</sub>d<sub>re</sub> T<sub>erm</sub>i<sub>er</sub> Uni<sub>v.</sub> R<sub>e</sub>nn<sub>es</sub> 1<sub>,</sub> Inri<sub>a,</sub> IRISA <sub>a</sub>l<sub>exan</sub>d<sub>re.</sub>t<sub>erm</sub>i<sub>er@</sub>i<sub>r</sub>i<sub>sa.</sub>f<sub>r</sub>

## ABSTRACT

A<sub>noma</sub>l<sub>y</sub> d<sub>e</sub>t<sub>ec</sub>ti<sub>on</sub> i<sub>n</sub> ti<sub>me</sub> <sub>ser</sub>i<sub>es</sub> h<sub>as</sub> <sub>a</sub>tt<sub>rac</sub>t<sub>e</sub>d <sub>cons</sub>id<sub>era</sub>bl<sub>e</sub> <sub>a</sub>t tention due to its im<sub>p</sub>ortance in man<sub>y</sub> real-world a<sub>pp</sub>lications in cludin<sub>g</sub> intrusion detection<sub>,</sub> ener<sub>gy</sub> mana<sub>g</sub>ement and finance. Most <sub>approac</sub>h<sub>es</sub> f<sub>or</sub> d<sub>e</sub>t<sub>ec</sub>ti<sub>ng</sub> <sub>ou</sub>tli<sub>ers</sub> <sub>re</sub>l<sub>y</sub> <sub>on</sub> <sub>e</sub>ith<sub>er</sub> <sub>manua</sub>ll<sub>y</sub> <sub>se</sub>t th<sub>res</sub>h<sub>-</sub> <sub>o</sub>ld<sub>s or assump</sub>ti<sub>ons on</sub> th<sub>e</sub> di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on o</sub>f d<sub>a</sub>t<sub>a accor</sub>di<sub>ng</sub> t<sub>o</sub> Ch<sub>an</sub> <sup>d</sup>o<sup>l</sup>a, Banerjee an<sup>d</sup> Kumar.

Here<sub>,</sub> we <sub>p</sub>ro<sub>p</sub>ose a new a<sub>pp</sub>roach to detect outliers in streamin<sub>g</sub> <sub>u</sub>ni<sub>va</sub>ri<sub>a</sub>t<sub>e</sub> tim<sub>e</sub> <sub>se</sub>ri<sub>es</sub> b<sub>ase</sub>d <sub>o</sub>n Extr<sub>e</sub>m<sub>e</sub> V<sub>a</sub>l<sub>ue</sub> Th<sub>eo</sub>r<sub>y</sub> th<sub>a</sub>t d<sub>oes</sub> <sub>no</sub>t <sub>requ</sub>i<sub>re</sub> t<sub>o</sub> h<sub>an</sub>d<sub>-se</sub>t th<sub>res</sub>h<sub>o</sub>ld<sub>s an</sub>d <sub>ma</sub>k<sub>es no assump</sub>ti<sub>on on</sub> the distribution: the main <sub>p</sub>arameter is onl<sub>y</sub> the risk<sub>,</sub> controllin<sub>g</sub> th<sub>e num</sub>b<sub>er o</sub>f f<sub>a</sub>l<sub>se pos</sub>iti<sub>ves.</sub> O<sub>ur approac</sub>h <sub>can</sub> b<sub>e use</sub>d f<sub>or ou</sub>tli<sub>er</sub> d<sub>e</sub>t<sub>ec</sub>ti<sub>on,</sub> b<sub>u</sub>t <sub>more genera</sub>ll<sub>y</sub> f<sub>or au</sub>t<sub>oma</sub>ti<sub>ca</sub>ll<sub>y se</sub>tti<sub>ng</sub> th<sub>res</sub>h<sub>o</sub>ld<sub>s,</sub> makin<sub>g</sub> it useful in wide number of situations. We also ex<sub>p</sub>eriment <sub>our a</sub>l<sub>gor</sub>ith<sub>ms on var</sub>i<sub>ous rea</sub>l<sub>-wor</sub>ld d<sub>a</sub>t<sub>ase</sub>t<sub>s w</sub>hi<sub>c</sub>h <sub>con</sub>fi<sub>rm</sub> it<sub>s</sub> <sub>soun</sub>d<sub>ness</sub> <sub>an</sub>d <sub>e</sub>fi<sub>c</sub>i<sub>ency.</sub>

## CCS CONCEPTS

• Computing methodologies → Anomaly detection; • Math ematics of computing → Time series analysis; • Information systems → Data stream mining;

## KEYWORDS

O<sub>u</sub>tli<sub>e</sub>r<sub>s</sub> in tim<sub>e</sub> <sub>se</sub>ri<sub>es,</sub> Extr<sub>e</sub>m<sub>e</sub> V<sub>a</sub>l<sub>ue</sub> Th<sub>eo</sub>r<sub>y,</sub> Str<sub>ea</sub>min<sub>g</sub>

## 1 INTRODUCTION

Anomal<sub>y</sub> detection is an im<sub>p</sub>ortant research area in data minin<sub>g</sub>. Many types of anomalies, or outliers, are described in the litera ture [23]. One of the most fundamental t<sub>yp</sub>e of anomalies are the extreme values (maximum and minimum).

M<sub>any wor</sub>k h<sub>ave</sub> b<sub>een propose</sub>d f<sub>or so</sub>l<sub>v</sub>i<sub>ng</sub> thi<sub>s pro</sub>bl<sub>em.</sub> H<sub>ow</sub> <sub>ever,</sub> th<sub>ey</sub> <sub>requ</sub>i<sub>re</sub> <sub>some</sub> k<sub>now</sub>l<sub>e</sub>d<sub>ge</sub> <sub>a</sub>b<sub>ou</sub>t th<sub>e</sub> d<sub>a</sub>t<sub>a:</sub> <sub>e</sub>ith<sub>er</sub> th<sub>ey</sub> <sub>ma</sub>k<sub>e</sub> assum<sub>p</sub>tions on the underl<sub>y</sub>in<sub>g</sub> distribution or the<sub>y</sub> need manuall<sub>y</sub> <sub>se</sub>t th<sub>res</sub>h<sub>o</sub>ld<sub>s.</sub>

Pi<sub>e</sub>rr<sub>e</sub>-Al<sub>a</sub>in F<sub>ouque</sub> Uni<sub>v.</sub> R<sub>e</sub>nn<sub>es</sub> 1<sub>,</sub> IUF<sub>,</sub> IRISA <sub>p</sub>i<sub>erre-a</sub>l<sub>a</sub>i<sub>n.</sub>f<sub>ouque@</sub>i<sub>nr</sub>i<sub>a.</sub>f<sub>r</sub>

Chri<sub>s</sub>tin<sub>e</sub> L<sub>a</sub>r<sub>goue</sub>t A<sub>g</sub>r<sub>o</sub>C<sub>a</sub>m<sub>pus,</sub> Inri<sub>a,</sub> IRISA <sub>c</sub>h<sub>r</sub>i<sub>s</sub>ti<sub>ne.</sub>l<sub>argoue</sub>t<sub>@</sub>i<sub>r</sub>i<sub>sa.</sub>f<sub>r</sub>

When the data is static<sub>,</sub> or is a stream comin<sub>g</sub> from an extremel<sub>y</sub> <sub>con</sub>t<sub>ro</sub>ll<sub>e</sub>d <sub>env</sub>i<sub>ronmen</sub>t<sub>,</sub> <sub>suc</sub>h <sub>assump</sub>ti<sub>ons</sub> <sub>can</sub> <sub>sa</sub>f<sub>e</sub>l<sub>y</sub> b<sub>e</sub> <sub>ma</sub>d<sub>e.</sub> B<sub>u</sub>t in the <sub>g</sub>eneral case of streamin<sub>g</sub> data from an o<sub>p</sub>en environment<sub>,</sub> these assum<sub>p</sub>tions are no lon<sub>g</sub>er true. The<sub>y</sub> ma<sub>y</sub> fail in unex<sub>p</sub>ected cases.

The issue is that nowada<sub>y</sub>s<sub>,</sub> more and more critical a<sub>pp</sub>lications rely on high throughput streaming numerical data like energy mana<sub>g</sub>ement [30], c<sub>y</sub>ber-securit<sub>y</sub> [32] or finance [26]. For exam<sub>p</sub>le, in intrusion detection<sub>,</sub> some network attack techni<sub>q</sub>ues rel<sub>y</sub> on inten-<sub>s</sub>i<sub>ve scans o</sub>f th<sub>e ne</sub>t<sub>wor</sub>k<sub>, w</sub>hi<sub>c</sub>h <sub>are c</sub>h<sub>arac</sub>t<sub>er</sub>i<sub>ze</sub>d b<sub>y an unusua</sub>ll<sub>y</sub> hi<sub>g</sub>h number of SYN <sub>p</sub>ackets [32].

Th<sub>e</sub> <sub>ma</sub>i<sub>n</sub> <sub>c</sub>h<sub>a</sub>ll<sub>enge</sub> i<sub>s</sub> t<sub>o</sub> l<sub>earn</sub> “<sub>norma</sub>lit<sub>y</sub>" i<sub>n</sub> <sub>an</sub> <sub>ever</sub> <sub>c</sub>h<sub>ang-</sub> i<sub>ng</sub> <sub>env</sub>i<sub>ronmen</sub>t <sub>an</sub>d t<sub>o</sub> <sub>au</sub>t<sub>oma</sub>ti<sub>ca</sub>ll<sub>y</sub> <sub>a</sub>d<sub>ap</sub>t th<sub>e</sub> d<sub>e</sub>t<sub>ec</sub>ti<sub>on</sub> <sub>me</sub>th<sub>o</sub>d accordin<sub>g</sub>l<sub>y</sub>.

Th<sub>e pro</sub>bl<sub>em o</sub>f d<sub>e</sub>t<sub>ec</sub>ti<sub>ng ex</sub>t<sub>reme va</sub>l<sub>ues</sub> i<sub>n s</sub>t<sub>reams can</sub> b<sub>e ex-</sub> <sub>presse</sub>d <sub>as</sub> f<sub>o</sub>ll<sub>ows:</sub> L<sub>e</sub>t $( X _ { t } ) _ { t \geq 0 }$ b<sub>e a s</sub>tr<sub>ea</sub>min<sub>g</sub> tim<sub>e se</sub>ri<sub>es o</sub>f iid <sub>o</sub>b<sub>serva</sub>ti<sub>ons.</sub> C<sub>an</sub> <sub>we</sub> <sub>se</sub>t <sub>a</sub> th<sub>res</sub>h<sub>o</sub>ld $z _ { q }$ <sub>suc</sub>h th<sub>a</sub>t f<sub>or</sub> <sub>any</sub> $t \geq 0 ,$ th<sub>e pro</sub>b<sub>a</sub>bilit<sub>y</sub> t<sub>o o</sub>b<sub>serve</sub> $X _ { t } > z _ { q }$ is lower than <sub>q</sub> (for <sub>q</sub> as small as desired) ?

T<sub>o so</sub>l<sub>ve</sub> thi<sub>s pro</sub>bl<sub>em, we use</sub> th<sub>e s</sub>t<sub>a</sub>ti<sub>s</sub>ti<sub>ca</sub>l <sub>power</sub>f<sub>u</sub>l t<sub>oo</sub>l <sub>o</sub>f Extreme Value Theory (EVT). This theory was developed to study the l<sub>aw o</sub>f <sub>ex</sub>t<sub>reme va</sub>l<sub>ues</sub> i<sub>n a</sub> di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on</sub> f<sub>unc</sub>ti<sub>on a</sub>ft<sub>er</sub> th<sub>e</sub> f<sub>o</sub>ll<sub>ow</sub>i<sub>ng</sub> dramatic event. In the ni<sub>g</sub>ht of Januar<sub>y</sub> 31 to Februar<sub>y</sub> 1 of the <sub>y</sub>ear 1953<sub>, a se</sub>t <sub>o</sub>f <sub>rare con</sub>diti<sub>ons occurre</sub>d i<sub>n</sub> th<sub>e</sub> N<sub>or</sub>th S<sub>ea,</sub> l<sub>ea</sub>di<sub>ng</sub> t<sub>o</sub> <sub>a</sub> “<sub>per</sub>f<sub>ec</sub>t <sub>s</sub>t<sub>orm</sub>” <sub>scenar</sub>i<sub>o.</sub> O<sub>n</sub> th<sub>e</sub> <sub>coas</sub>t <sub>o</sub>f N<sub>e</sub>th<sub>er</sub>l<sub>an</sub>d<sub>s,</sub> th<sub>e</sub> <sub>waves</sub> <sub>genera</sub>t<sub>e</sub>d <sub>overw</sub>h<sub>e</sub>l<sub>me</sub>d th<sub>e</sub> dik<sub>es,</sub> <sub>caus</sub>i<sub>ng</sub> <sub>ex</sub>t<sub>ens</sub>i<sub>ve</sub> fl<sub>oo</sub>di<sub>ng.</sub> Th<sub>e</sub> fl<sub>oo</sub>di<sub>ng</sub> l<sub>e</sub>d t<sub>o</sub> th<sub>e</sub> d<sub>ea</sub>th <sub>o</sub>f 1800<sub>+ peop</sub>l<sub>e</sub> i<sub>n</sub> th<sub>e</sub> N<sub>e</sub>th<sub>er</sub>l<sub>an</sub>d<sub>s a</sub>l<sub>one.</sub> I<sub>n</sub> th<sub>e</sub> dik<sub>e case,</sub> $X _ { t }$ i<sub>s</sub> th<sub>e</sub> h<sub>e</sub>i<sub>g</sub>ht <sub>o</sub>f th<sub>e waves, an</sub>d $z _ { q }$ i<sub>s</sub> th<sub>e</sub> h<sub>e</sub>i<sub>g</sub>ht <sub>o</sub>f th<sub>e</sub> dik<sub>e.</sub>

I<sub>n</sub> th<sub>e a</sub>ft<sub>erma</sub>th <sub>o</sub>f thi<sub>s</sub> di<sub>sas</sub>t<sub>er, sc</sub>i<sub>en</sub>ti<sub>s</sub>t<sub>s were</sub> t<sub>as</sub>k<sub>e</sub>d t<sub>o</sub> d<sub>e</sub>t<sub>er-</sub> <sub>m</sub>i<sub>ne a m</sub>i<sub>n</sub>i<sub>ma</sub>l dik<sub>e</sub> h<sub>e</sub>i<sub>g</sub>ht <sub>suc</sub>h th<sub>a</sub>t th<sub>e pro</sub>b<sub>a</sub>bilit<sub>y</sub> f<sub>or waves</sub> t<sub>o</sub> exceed this hei<sub>g</sub>ht is extremel<sub>y</sub> low. Statisticians devised an ele<sub>g</sub>ant theor<sub>y</sub> for the stud<sub>y</sub> of such rare events [10]. One of the most ele-<sub>gan</sub>t <sub>resu</sub>lt <sub>o</sub>f EVT i<sub>s</sub> th<sub>a</sub>t th<sub>e</sub> di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on o</sub>f th<sub>e ex</sub>t<sub>reme va</sub>l<sub>ues</sub> i<sub>s</sub> <sub>a</sub>l<sub>mos</sub>t i<sub>n</sub>d<sub>epen</sub>d<sub>en</sub>t <sub>o</sub>f th<sub>e</sub> di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on o</sub>f th<sub>e</sub> d<sub>a</sub>t<sub>a w</sub>ith <sub>a</sub> th<sub>eorem</sub> <sub>s</sub>i<sub>m</sub>il<sub>ar</sub> t<sub>o</sub> th<sub>e cen</sub>t<sub>ra</sub>l li<sub>m</sub>it th<sub>eorem,</sub> f<sub>or m</sub>i<sub>n max</sub> i<sub>ns</sub>t<sub>ea</sub>d <sub>o</sub>f th<sub>e</sub> <sub>mean</sub> <sub>va</sub>l<sub>ue.</sub>

The main contribution of this <sub>p</sub>a<sub>p</sub>er is to <sub>p</sub>ro<sub>p</sub>ose an a<sub>pp</sub>roach for outlier detection in hi<sub>g</sub>h throu<sub>g</sub>h<sub>p</sub>ut streamin<sub>g</sub> univariate and <sub>u</sub>nimodal time series. Thanks to EVT<sub>,</sub> o<sub>u</sub>r a<sub>pp</sub>roach makes no dist<sub>r</sub>ib<sub>u</sub>ti<sub>on assump</sub>ti<sub>on on</sub> th<sub>e</sub> d<sub>a</sub>t<sub>a:</sub> it i<sub>s</sub> th<sub>us a so</sub>l<sub>u</sub>ti<sub>on</sub> t<sub>o</sub> “R<sub>esearc</sub>h I<sub>ssue</sub> $6 "$ f<sub>or ou</sub>tli<sub>er</sub> d<sub>e</sub>t<sub>ec</sub>ti<sub>on</sub> i<sub>n</sub> d<sub>a</sub>t<sub>a s</sub>t<sub>reams as s</sub>t<sub>a</sub>t<sub>e</sub>d b<sub>y</sub> S<sub>a</sub>dik and Gruenwald [29] in SIGKDD Explorations 2014. We decline our a<sub>pp</sub>roach into two al<sub>g</sub>orithms: SPOT for streamin<sub>g</sub> data havin<sub>g</sub> an<sub>y</sub> <sub>s</sub>t<sub>a</sub>ti<sub>o</sub>n<sub>a</sub>r<sub>y</sub> di<sub>s</sub>trib<sub>u</sub>ti<sub>o</sub>n<sub>,</sub> <sub>a</sub>nd DSPOT f<sub>o</sub>r <sub>s</sub>tr<sub>ea</sub>min<sub>g</sub> d<sub>a</sub>t<sub>a</sub> th<sub>a</sub>t <sub>ca</sub>n b<sub>e</sub> su<sup>b</sup>ject to concept <sup>d</sup>ri<sup>f</sup>t. T<sup>h</sup>roug<sup>h d</sup>etai<sup>l</sup>e<sup>d</sup> experiments on synt<sup>h</sup>etic <sub>an</sub>d <sub>rea</sub>l d<sub>a</sub>t<sub>a, we s</sub>h<sub>ow</sub> th<sub>a</sub>t <sub>our approac</sub>h i<sub>s accura</sub>t<sub>e</sub> f<sub>or</sub> d<sub>e</sub>t<sub>ec</sub>ti<sub>ng</sub> o<sub>u</sub>tliers<sub>,</sub> is com<sub>pu</sub>tationall<sub>y</sub> eficient<sub>,</sub> and for DSPOT reacts <sub>qu</sub>ickl<sub>y</sub> to an<sub>y</sub> chan<sub>g</sub>e in the stream. For instance<sub>,</sub> we decide to test our al<sub>g</sub>orithm on incomin<sub>g</sub> streams without knowled<sub>g</sub>e on their distri bution. We show that we detect ver<sub>y</sub> eficientl<sub>y</sub> and accuratel<sub>y</sub>: (i) network SYN attacks on a labeled data stream and (ii) peaks that allows to take decision on stock market (<sub>q</sub>uickl<sub>y</sub> react for bu<sub>y</sub>in<sub>g</sub> or sellin<sub>g</sub> shares). Our ex<sub>p</sub>eriments also confirm the EVT theor<sub>y</sub> <sub>w</sub>ith <sub>accuracy</sub> <sub>an</sub>d f<sub>as</sub>t <sub>convergence.</sub>

Anal<sub>y</sub>zin<sub>g</sub> streamin<sub>g</sub> data re<sub>q</sub>uire the com<sub>p</sub>utation of EVT to be fast and resilient: as a secondar<sub>y</sub> contribution<sub>,</sub> we <sub>p</sub>ro<sub>p</sub>ose two i<sub>mprovemen</sub>t<sub>s</sub> <sub>on</sub> th<sub>e</sub> <sub>genera</sub>l <sub>me</sub>th<sub>o</sub>d f<sub>or</sub> <sub>so</sub>l<sub>v</sub>i<sub>ng</sub> th<sub>e</sub> EVT <sub>pro</sub>bl<sub>em,</sub> th<sub>a</sub>t i<sub>mprove</sub> b<sub>o</sub>th it<sub>s spee</sub>d <sub>an</sub>d it<sub>s ro</sub>b<sub>us</sub>t<sub>ness.</sub> Th<sub>ey are use</sub>d i<sub>n</sub> <sub>our a</sub>l<sub>gor</sub>ith<sub>ms,</sub> b<sub>u</sub>t th<sub>ey are no</sub>t <sub>spec</sub>ifi<sub>c</sub> t<sub>o s</sub>t<sub>ream</sub>i<sub>ng</sub> d<sub>a</sub>t<sub>a an</sub>d <sub>can</sub> immediatel<sub>y</sub> be a<sub>pp</sub>lied to most al<sub>g</sub>orithms usin<sub>g</sub> EVT.

## 2 RELATED WORK

Cl<sub>ass</sub>i<sub>ca</sub>ll<sub>y, anoma</sub>l<sub>y</sub> d<sub>e</sub>t<sub>ec</sub>t<sub>ors</sub> h<sub>ave</sub> t<sub>o</sub> hi<sub>g</sub>hli<sub>g</sub>ht <sub>w</sub>h<sub>a</sub>t <sub>w</sub>ill b<sub>e con-</sub> sidered as an anomaly, also called outlier. As we propose a statistical <sub>me</sub>th<sub>o</sub>d t<sub>o</sub> fi<sub>n</sub>d <sub>anoma</sub>li<sub>es,</sub> <sub>we</sub> <sub>re</sub>l<sub>y</sub> <sub>on</sub> th<sub>e</sub> <sub>assump</sub>ti<sub>on</sub> <sub>g</sub>i<sub>ven</sub> b<sub>y</sub> Ch<sub>an</sub> dola, Banerjee and Kumar in [13]: “Normal data instances occur i<sub>n</sub> hi<sub>g</sub>h <sub>pro</sub>b<sub>a</sub>bilit<sub>y reg</sub>i<sub>ons o</sub>f <sub>a s</sub>t<sub>oc</sub>h<sub>as</sub>ti<sub>c mo</sub>d<sub>e</sub>l<sub>, w</sub>hil<sub>e anoma</sub>li<sub>es</sub> <sub>occur</sub> i<sub>n</sub> th<sub>e</sub> l<sub>ow pro</sub>b<sub>a</sub>bilit<sub>y reg</sub>i<sub>ons o</sub>f th<sub>e s</sub>t<sub>oc</sub>h<sub>as</sub>ti<sub>c mo</sub>d<sub>e</sub>l”<sub>.</sub>

A <sub>g</sub>reat deal of al<sub>g</sub>orithms for static outlier detection are <sub>g</sub>iven in the literature. The main a<sub>pp</sub>roaches are distance based [7], nearest nei<sub>g</sub>hbor based [11] or clusterin<sub>g</sub> based [14] and are ver<sub>y</sub> well detailed in [13]. Nonetheless, as mentioned in [31], most existin<sub>g</sub> <sub>ou</sub>tli<sub>er</sub> d<sub>e</sub>t<sub>ec</sub>ti<sub>on</sub> <sub>me</sub>th<sub>o</sub>d<sub>s</sub> <sub>nee</sub>d t<sub>o</sub> <sub>scan</sub> <sub>severa</sub>l ti<sub>mes</sub> th<sub>e</sub> d<sub>a</sub>t<sub>a</sub> <sub>an</sub>d/<sub>or</sub> h<sub>ave</sub> hi<sub>g</sub>h ti<sub>me</sub> <sub>comp</sub>l<sub>ex</sub>it<sub>y,</sub> th<sub>us</sub> th<sub>ey</sub> <sub>canno</sub>t b<sub>e</sub> <sub>use</sub>d i<sub>n</sub> d<sub>a</sub>t<sub>a</sub> <sub>s</sub>t<sub>reams.</sub>

In [28, 29], Sadik details the s<sub>p</sub>ecificities of the stream environ-<sub>men</sub>t <sub>an</sub>d th<sub>e</sub> h<sub>ar</sub>d<sub>s</sub>hi<sub>ps</sub> <sub>o</sub>f <sub>ou</sub>tli<sub>er</sub> d<sub>e</sub>t<sub>ec</sub>ti<sub>on</sub> i<sub>n</sub> thi<sub>s</sub> <sub>con</sub>t<sub>ex</sub>t<sub>.</sub> Th<sub>e</sub> <sub>ma</sub>i<sub>n cons</sub>t<sub>ra</sub>i<sub>n</sub>t<sub>s are</sub> th<sub>e</sub> f<sub>o</sub>ll<sub>ow</sub>i<sub>ng:</sub> d<sub>a</sub>t<sub>a canno</sub>t b<sub>e scanne</sub>d t<sub>w</sub>i<sub>ce</sub> an<sup>d</sup> new conce<sub>p</sub>ts ma<sub>y</sub> <sup>k</sup>ee<sub>p</sub> evo<sup>l</sup>v<sup>i</sup>n<sub>g</sub>.

M<sub>any</sub> <sub>wor</sub>k<sub>s</sub> <sub>w</sub>hi<sub>c</sub>h <sub>a</sub>dd<sub>ress</sub> th<sub>e</sub> <sub>s</sub>t<sub>ream</sub>i<sub>ng</sub> <sub>case</sub> <sub>presen</sub>t di<sub>s</sub>t<sub>ance</sub> based al<sub>g</sub>orithms for outlier detection (STORM [8], CORM [15], DBOD-DS [28], attributes wei<sub>g</sub>htin<sub>g</sub> [31]). These methods are able t<sub>o</sub> <sub>wor</sub>k <sub>on</sub> <sub>mu</sub>ltidi<sub>mens</sub>i<sub>ona</sub>l <sub>s</sub>t<sub>reams</sub> <sub>w</sub>ith <sub>ca</sub>t<sub>egor</sub>i<sub>ca</sub>l f<sub>ea</sub>t<sub>ures</sub> b<sub>u</sub>t th<sub>ey nee</sub>d <sub>user</sub> d<sub>e</sub>fi<sub>ne</sub>d th<sub>res</sub>h<sub>o</sub>ld<sub>s w</sub>hi<sub>c</sub>h <sub>cou</sub>ld b<sub>e a rea</sub>l hi<sub>n</sub>d<sub>rance</sub> in <sub>p</sub>r<sub>ac</sub>ti<sub>ce.</sub>

Current statistical a<sub>pp</sub>roaches to <sub>p</sub>erform outlier detection in d<sub>a</sub>t<sub>a s</sub>t<sub>ream su</sub>f<sub>er</sub> f<sub>rom</sub> th<sub>e</sub> i<sub>n</sub>h<sub>eren</sub>t <sub>pro</sub>bl<sub>em, name</sub>l<sub>y</sub> th<sub>e</sub> di<sub>s</sub>t<sub>r</sub>i bution assum<sub>p</sub>tion. In [6], A<sub>g</sub>arwal assumes a <sub>g</sub>aussian model to d<sub>e</sub>t<sub>ec</sub>t <sub>anoma</sub>li<sub>es</sub> i<sub>n mu</sub>ltidi<sub>mens</sub>i<sub>ona</sub>l <sub>arrays an</sub>d <sub>recommen</sub>d<sub>s a</sub> Box-Cox transformation if it is not the case. In [16], a more <sub>g</sub>eneral mixture mo<sup>d</sup>e<sup>l</sup> is presente<sup>d b</sup>y Es<sup>k</sup>in, <sup>b</sup>ase<sup>d</sup> on a majority <sup>d</sup>istri<sup>b</sup>u ti<sub>on an</sub>d <sub>an anoma</sub>l<sub>y one.</sub> H<sub>owever</sub> b<sub>o</sub>th <sub>mo</sub>d<sub>e</sub>l<sub>s nee</sub>d t<sub>o</sub> b<sub>e</sub> l<sub>earne</sub>d<sub>,</sub> so data of each distribution are re<sub>q</sub>uired. In [24], the authors use <sub>a pro</sub>b<sub>a</sub>bili<sub>s</sub>t th<sub>res</sub>h<sub>o</sub>ld <sub>ϵ</sub> t<sub>o</sub> di<sub>scr</sub>i<sub>m</sub>i<sub>na</sub>t<sub>e norma</sub>l <sub>or a</sub>b<sub>norma</sub>l d<sub>a</sub>t<sub>a</sub> (observations with <sub>p</sub>robabilit<sub>y</sub> lower than <sub>ϵ</sub> are anomalies), but it<sub>s poss</sub>ibl<sub>e va</sub>l<sub>ues are</sub> l<sub>ower-</sub>b<sub>oun</sub>d<sub>e</sub>d b<sub>y</sub> $1 / ( k + 1 )$ where k is the number of trainin<sub>g</sub> elements. Thus it needs a hu<sub>g</sub>e trainin<sub>g</sub> sam<sub>p</sub>le if we want a ver<sub>y</sub> low false <sub>p</sub>ositive rate.

I<sub>n</sub> <sub>our</sub> <sub>wor</sub>k<sub>,</sub> <sub>we</sub> d<sub>o</sub> <sub>no</sub>t <sub>assume</sub> th<sub>e</sub> di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on</sub> <sub>o</sub>f th<sub>e</sub> <sub>va</sub>l<sub>ue</sub> <sub>we</sub> <sub>mon</sub>it<sub>or</sub> b<sub>u</sub>t <sub>we</sub> <sub>re</sub>l<sub>y</sub> <sub>on</sub> <sub>power</sub>f<sub>u</sub>l th<sub>eore</sub>ti<sub>ca</sub>l <sub>resu</sub>lt<sub>s</sub> t<sub>o</sub> <sub>es</sub>ti<sub>ma</sub>t<sub>e</sub> <sub>accura</sub>t<sub>e</sub>l<sub>y</sub> l<sub>ow pro</sub>b<sub>a</sub>bilit<sub>y areas an</sub>d th<sub>en</sub> di<sub>scr</sub>i<sub>m</sub>i<sub>na</sub>t<sub>e ou</sub>tli<sub>ers.</sub>

With <sub>our s</sub>i<sub>ng</sub>l<sub>e parame</sub>t<sub>er a</sub>l<sub>gor</sub>ith<sub>ms, we are a</sub>bl<sub>e</sub> t<sub>o</sub> d<sub>e</sub>t<sub>ec</sub>t <sub>ou</sub>tli<sub>ers</sub> in both stationar<sub>y</sub> and driftin<sub>g</sub> contexts.

## 3 BACKGROUND

I<sub>n</sub> thi<sub>s sec</sub>ti<sub>on we</sub> d<sub>escr</sub>ib<sub>e</sub> th<sub>e</sub> th<sub>eore</sub>ti<sub>ca</sub>l b<sub>ac</sub>k<sub>groun</sub>d <sub>o</sub>f th<sub>e</sub> E<sub>x-</sub> treme Value Theor<sub>y</sub> (EVT). We tr<sub>y</sub> to ex<sub>p</sub>lain the main results and how the<sub>y</sub> could be used to address our <sub>p</sub>roblem (the reader could refer to the rich reference of Beirlant et al. [10] for more details). This <sub>p</sub>art is not a <sub>p</sub>rere<sub>q</sub>uisite to understand the <sub>p</sub>ur<sub>p</sub>ose of our <sub>a</sub>l<sub>gor</sub>ith<sub>m</sub> b<sub>u</sub>t it <sub>ga</sub>th<sub>ers</sub> <sub>some</sub> <sub>e</sub>l<sub>emen</sub>t<sub>s</sub> t<sub>o</sub> <sub>prec</sub>i<sub>se</sub> it<sub>s</sub> f<sub>un</sub>d<sub>amen</sub>t<sub>a</sub>l b<sub>as</sub>i<sub>s.</sub>

M<sub>any</sub> t<sub>ec</sub>h<sub>n</sub>i<sub>ques a</sub>ll<sub>ow</sub> th<sub>e sc</sub>i<sub>en</sub>ti<sub>s</sub>t t<sub>o</sub> fi<sub>n</sub>d <sub>s</sub>t<sub>a</sub>ti<sub>s</sub>ti<sub>ca</sub>l th<sub>res</sub>h<sub>-</sub> olds (<sub>q</sub>uantiles). For instance, we can com<sub>p</sub>ute them em<sub>p</sub>iricall<sub>y</sub> <sub>or</sub> <sub>assume</sub> <sub>a</sub> di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on.</sub> H<sub>owever</sub> d<sub>a</sub>t<sub>a</sub> d<sub>o</sub> <sub>no</sub>t <sub>necessar</sub>il<sub>y</sub> f<sub>o</sub>ll<sub>ow</sub> well-known distributions (Gaussian, uniform, ex<sub>p</sub>onential etc.) so the model ste<sub>p</sub> (the choice of the distribution) could be hard, even inappropriate. Moreover, if we want to predict extreme events, like rare or un<sub>p</sub>recedented events (as tidal waves), the em<sub>p</sub>irical method will not <sub>g</sub>ive accurate estimation (an un<sub>p</sub>recedented event would have a <sub>p</sub>robabilit<sub>y</sub> e<sub>q</sub>ual to zero). The extreme value theor<sub>y</sub> add<sub>resses</sub> th<sub>ese pro</sub>bl<sub>ems</sub> b<sub>y</sub> i<sub>n</sub>f<sub>err</sub>i<sub>ng</sub> th<sub>e</sub> di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on o</sub>f th<sub>e ex</sub>t<sub>reme</sub> events we mi<sub>g</sub>ht monitor<sub>,</sub> without stron<sub>g</sub> h<sub>yp</sub>othesis on the ori<sub>g</sub>inal di<sub>s</sub>trib<sub>u</sub>ti<sub>o</sub>n<sub>.</sub>

Mat<sup>h</sup>ematica<sup>ll</sup>y, X is a ran<sup>d</sup>om varia<sup>bl</sup>e an<sup>d</sup> F its cumu<sup>l</sup>ative di<sub>s</sub>trib<sub>u</sub>ti<sub>o</sub>n f<sub>u</sub>n<sub>c</sub>ti<sub>o</sub>n: $F ( x ) = \mathbb { P } ( X \leq x )$ . We <sup>d</sup>enote <sup>b</sup> F<sup>¯</sup> t<sup>h</sup>e <sup>“</sup>tai<sup>l</sup>" o<sup>f</sup> th<sub>e</sub> di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on:</sub> ${ \bar { F } } ( x ) = 1 - F ( x ) = \mathbb { P } ( X > x )$ . We use $X _ { i }$ t<sub>o</sub> d<sub>eno</sub>t<sub>e</sub> b<sub>o</sub>th <sub>ran</sub>d<sub>om var</sub>i<sub>a</sub>bl<sub>es an</sub>d th<sub>e</sub>i<sub>r ou</sub>t<sub>comes,</sub> h<sub>owever</sub> th<sub>e con</sub>t<sub>ex</sub>t wi<sup>ll</sup> precise t<sup>h</sup>eir meanings. For a ran<sup>d</sup>om varia<sup>bl</sup>e X an<sup>d</sup> a given <sub>p</sub>robabilit<sub>y q</sub> we note $z _ { q }$ it<sub>s quan</sub>til<sub>e a</sub>t l<sub>eve</sub>l $1 - q ,$ i<sub>.e.</sub> $z _ { q }$ i<sub>s</sub> th<sub>e</sub> <sub>sma</sub>ll<sub>es</sub>t <sub>va</sub>l<sub>ue s.</sub>t<sub>.</sub> $\mathbb { P } ( X \leq z _ { q } ) \geq 1 - q { \mathrm { ~ i . e . ~ } } \mathbb { P } ( X > z _ { q } ) < q .$

## 3.1 Extreme value distributions

Th<sub>e goa</sub>l <sub>o</sub>f th<sub>e ex</sub>t<sub>reme va</sub>l<sub>ue</sub> th<sub>eory</sub> i<sub>s</sub> t<sub>o</sub> fi<sub>n</sub>d th<sub>e</sub> l<sub>aw o</sub>f <sub>ex</sub>t<sub>reme</sub> events (e.<sub>g</sub>. the law of the dail<sub>y</sub> maximum of tem<sub>p</sub>erature, or the law of the monthl<sub>y</sub> maximal tide hei<sub>g</sub>ht). A beautiful result from Fisher, Ti<sub>pp</sub>ett [18] and later Gnedenko [20] states that, under a <sub>wea</sub>k <sub>con</sub>diti<sub>on,</sub> th<sub>ese ex</sub>t<sub>reme even</sub>t<sub>s</sub> h<sub>ave</sub> th<sub>e same</sub> ki<sub>n</sub>d <sub>o</sub>f di<sub>s</sub>t<sub>r</sub>i<sub>-</sub> bution<sub>,</sub> re<sub>g</sub>ardless of the ori<sub>g</sub>inal one. For instance the maximum <sub>o</sub>f t<sub>empera</sub>t<sub>ures or</sub> tid<sub>e</sub> h<sub>e</sub>i<sub>g</sub>ht<sub>s</sub> h<sub>ave more or</sub> l<sub>ess</sub> th<sub>e same</sub> di<sub>s</sub>t<sub>r</sub>i<sub>-</sub> b<sub>u</sub>ti<sub>on</sub> <sub>w</sub>h<sub>ereas</sub> th<sub>e</sub> di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>ons</sub> <sub>o</sub>f th<sub>e</sub> t<sub>empera</sub>t<sub>ures</sub> <sub>an</sub>d th<sub>e</sub> tid<sub>e</sub> h<sub>e</sub>i<sub>g</sub>ht<sub>s</sub> <sub>are</sub> <sub>no</sub>t lik<sub>e</sub>l<sub>y</sub> t<sub>o</sub> b<sub>e</sub> th<sub>e</sub> <sub>same.</sub> Thi<sub>s</sub> <sub>ex</sub>t<sub>reme</sub> l<sub>aws</sub> <sub>are</sub> <sub>ca</sub>ll<sub>e</sub>d the Extreme Value Distributions (EVD) and the<sub>y</sub> have the followin<sub>g</sub> f<sub>orm</sub> <sub>:</sub>

$$
G _ {\gamma}: x \mapsto \exp \left(- (1 + \gamma x) ^ {- \frac {1}{\gamma}}\right), \quad \gamma \in \mathbb {R}, \quad 1 + \gamma x > 0.
$$

All th<sub>e ex</sub>t<sub>remes o</sub>f <sub>common s</sub>t<sub>an</sub>d<sub>ar</sub>d di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>ons</sub> f<sub>o</sub>ll<sub>ow suc</sub>h <sub>a</sub> distribution and the extreme value index γ depends on this original l<sub>aw.</sub> F<sub>or examp</sub>l<sub>e,</sub> if $X _ { 1 } , \dots X _ { n }$ are <sub>n</sub> iid variables (e.<sub>g</sub>. <sub>g</sub>aussian $N ( 0 , 1 ) )$ th<sub>en</sub> $M _ { n } = \operatorname* { m a x } _ { 1 \leq i \leq n } X _ { i }$ i<sub>s</sub> lik<sub>e</sub>l<sub>y</sub> t<sub>o</sub> f<sub>o</sub>ll<sub>ow an</sub> EVD <sub>w</sub>hi<sub>c</sub>h extreme value index <sub>γ</sub> is <sub>g</sub>iven b<sub>y</sub> the initial distribution (for the G<sub>auss</sub>i<sub>a</sub>n di<sub>s</sub>trib<sub>u</sub>ti<sub>o</sub>n $\gamma = 0 )$

This res<sub>u</sub>lt ma<sub>y</sub> seem <sub>v</sub>er<sub>y</sub> co<sub>u</sub>nterint<sub>u</sub>iti<sub>v</sub>e b<sub>u</sub>t <sub>w</sub>e can <sub>g</sub>i<sub>v</sub>e <sub>some</sub> <sub>e</sub>l<sub>emen</sub>t<sub>s</sub> t<sub>o</sub> <sub>ca</sub>t<sub>c</sub>h th<sub>e</sub> id<sub>ea.</sub> I<sub>n</sub>d<sub>ee</sub>d<sub>,</sub> <sub>we</sub> <sub>can</sub> <sub>eas</sub>il<sub>y</sub> i<sub>mag</sub>i<sub>ne</sub> th<sub>a</sub>t f<sub>or mos</sub>t di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>ons</sub> th<sub>e pro</sub>b<sub>a</sub>biliti<sub>es</sub> d<sub>ecrease w</sub>h<sub>en even</sub>t<sub>s are</sub> extreme<sub>,</sub> ie $\mathbb { P } ( X > x )  0$ <sub>w</sub>h<sub>en</sub> i<sub>ncreases.</sub> Th<sub>e</sub> f<sub>unc</sub>ti<sub>on</sub> $\bar { F } ( x ) =$ $\mathbb { P } ( X > x )$ represents the tail of the distribution of X. Actually, there <sub>are no</sub>t <sub>many poss</sub>ibl<sub>e s</sub>h<sub>apes</sub> f<sub>or</sub> thi<sub>s</sub> t<sub>a</sub>il <sub>an</sub>d $G _ { \gamma }$ t<sub>r</sub>i<sub>es</sub> t<sub>o</sub> fit th<sub>em.</sub> Th<sub>e</sub> t<sub>a</sub>bl<sub>e</sub> 1 <sub>presen</sub>t<sub>s</sub> th<sub>e</sub> th<sub>ree</sub> <sub>poss</sub>ibl<sub>e</sub> <sub>s</sub>h<sub>apes</sub> <sub>o</sub>f th<sub>e</sub> t<sub>a</sub>il <sub>an</sub>d th<sub>e</sub> li<sub>n</sub>k <sub>w</sub>ith th<sub>e</sub> <sub>ex</sub>t<sub>reme</sub> <sub>va</sub>l<sub>ue</sub> i<sub>n</sub>d<sub>ex</sub> <sub>γ</sub> <sub>.</sub> It <sub>g</sub>i<sub>ves</sub> <sub>a</sub>l<sub>so</sub> <sub>an</sub> <sub>examp</sub>l<sub>e</sub> <sub>o</sub>f <sub>s</sub>t<sub>an</sub>d<sub>ar</sub>d di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on w</sub>hi<sub>c</sub>h f<sub>o</sub>ll<sub>ows eac</sub>h t<sub>a</sub>il b<sub>e</sub>h<sub>av</sub>i<sub>or.</sub> Th<sub>e parame</sub>t<sub>er τ</sub> <sub>represen</sub>t<sub>s</sub> th<sub>e</sub> b<sub>oun</sub>d <sub>o</sub>f th<sub>e</sub> i<sub>n</sub>iti<sub>a</sub>l di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on, so</sub> it <sub>cou</sub>ld b<sub>e</sub> fi<sub>n</sub>it<sub>e</sub> (ex: uniform cdf) or infinite (ex: normal cdf). The fi<sub>g</sub>ure 1 de<sub>p</sub>icts <sub>an</sub> <sub>examp</sub>l<sub>e</sub> <sub>o</sub>f th<sub>e</sub> th<sub>ree</sub> b<sub>e</sub>h<sub>av</sub>i<sub>ors.</sub>

<table><tr><td>Tail behavior (x → τ)</td><td>Domain</td><td>Example</td></tr><tr><td>Heavy tail, P(X &gt; x) ≈ x-1/γ</td><td>γ &gt; 0</td><td>Frechet</td></tr><tr><td>Exponential tail, P(X &gt; x) ≈ e-x</td><td>γ = 0</td><td>Gamma</td></tr><tr><td>Bounded, P(X &gt; x) = 0</td><td>γ &lt; 0</td><td>Uniform</td></tr></table>

Table 1: Relation between F and γ

![](images/5a2e0b13c84bb8f835babe55fdb4a75770d58847025ad158cb16a29da623d3f8.jpg)  
Figure 1: Tail distribution $\bar { G } _ { \gamma }$ according to γ

## 3.2 Power of EVT

This <sub>p</sub>henomenon allo<sub>w</sub>s <sub>u</sub>s to acc<sub>u</sub>ratel<sub>y</sub> com<sub>pu</sub>te <sub>p</sub>robabilities <sub>w</sub>ith<sub>ou</sub>t i<sub>n</sub>f<sub>err</sub>i<sub>ng</sub> th<sub>e</sub> i<sub>n</sub>iti<sub>a</sub>l l<sub>aw</sub> th<sub>a</sub>t <sub>can</sub> b<sub>e</sub> <sub>rea</sub>ll<sub>y</sub> <sub>comp</sub>l<sub>ex.</sub> It “<sub>reg</sub> <sub>u</sub>l<sub>ar</sub>i<sub>zes</sub>" th<sub>e</sub> i<sub>n</sub>iti<sub>a</sub>l di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on.</sub> I<sub>n</sub>d<sub>ee</sub>d<sub>,</sub> th<sub>e</sub> <sub>cen</sub>t<sub>ra</sub>l li<sub>m</sub>it th<sub>eorem</sub> <sub>s</sub>t<sub>a</sub>t<sub>es</sub> th<sub>a</sub>t th<sub>e</sub> <sub>mean</sub> <sub>o</sub>f <sub>n</sub> iid <sub>ran</sub>d<sub>om</sub> <sub>var</sub>i<sub>a</sub>bl<sub>es</sub> <sub>converges</sub> i<sub>n</sub> di<sub>s</sub>t<sub>r</sub>i b<sub>u</sub>ti<sub>on</sub> t<sub>o a norma</sub>l di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on.</sub> Th<sub>e</sub> EVT th<sub>eorem s</sub>t<sub>a</sub>t<sub>es</sub> th<sub>e same</sub> <sub>resu</sub>lt f<sub>or</sub> th<sub>e max</sub>i<sub>mum.</sub>

![](images/bc5ea1279257d3d53f00a1b79ad8e7183ea0add82bd5fd6004082a99dd3f8cbc.jpg)  
Figure 2: EVD fit of an unknown cdf

B<sub>y</sub> fittin<sub>g</sub> an EVD to the <sub>u</sub>nkno<sub>w</sub>n in<sub>pu</sub>t distrib<sub>u</sub>tion tail (see fi<sub>g</sub>ure 2), it is then <sub>p</sub>ossibl<sub>e</sub> t<sub>o eva</sub>l<sub>ua</sub>t<sub>e</sub> th<sub>e pro</sub>b<sub>a</sub>bilit<sub>y</sub> of <sub>p</sub>otential extreme events. In <sub>p</sub>articular<sub>,</sub> from a <sub>g</sub>iven <sub>p</sub>robabilit<sub>y</sub> <sub>q</sub> it is <sub>p</sub>ossible to calcu l<sub>a</sub>t<sub>e</sub> $z _ { q }$ such that P(X $> z _ { q } ) <$ $q .$ T<sub>o so</sub>l<sub>ve</sub> thi<sub>s pro</sub>bl<sub>em,</sub> th<sub>e</sub> <sub>na</sub>t<sub>ura</sub>l <sub>way w</sub>ill b<sub>e</sub> t<sub>o es</sub>ti mate $\gamma .$ S<sub>eve</sub>r<sub>a</sub>l <sub>es</sub>tim<sub>a</sub>t<sub>es</sub> <sub>e</sub>xist such as Hill’s estimate [22] and Pickands’ estimate [27] but

the<sub>y g</sub>ive <sub>g</sub>ood results onl<sub>y</sub> for certain tail behaviors. Its estimati<sub>on</sub> i<sub>s</sub> h<sub>ar</sub>d <sub>an</sub>d <sub>nowa</sub>d<sub>ays</sub> <sub>we</sub> d<sub>o</sub> <sub>no</sub>t k<sub>now</sub> <sub>a</sub> <sub>genera</sub>l <sub>an</sub>d <sub>e</sub>fi<sub>c</sub>i<sub>en</sub>t method to com<sub>p</sub>ute it (i.e. for all $\gamma \in \mathbb { R } )$

A<sub>no</sub>th<sub>er</sub> <sub>way</sub> <sub>ex</sub>i<sub>s</sub>t<sub>s</sub> t<sub>o</sub> fit th<sub>e</sub> t<sub>a</sub>il <sub>o</sub>f th<sub>e</sub> di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on:</sub> th<sub>e</sub> P<sub>ea</sub>k<sub>s-</sub> Over-Threshold (POT) a<sub>pp</sub>roach.

## 3.3 Peaks-Over-Threshold (POT) approach

The Peaks-Over-Threshold (POT) a<sub>pp</sub>roach relies on the Pickands-Balkema-de Haan theorem [9, 27] (also called second theorem in EVT in com<sub>p</sub>arison to the initial result of Fisher, Ti<sub>pp</sub>ett and Gnedenko) <sub>g</sub>i<sub>ven</sub> b<sub>e</sub>l<sub>ow.</sub>

Theorem 3.1 (Pickands-Balkema-de Haan). The cumulative distribution function $F \in { \mathcal { D } _ { \gamma } } ^ { 1 }$ if and only if a function σ exists, for al $l x \in \mathbb { R } s . t . 1 + \gamma x > 0 .$

$$
\frac {\bar {F} (t + \sigma (t) x)}{\bar {F} (t)} \underset {t \to \tau} {\longrightarrow} (1 + \gamma x) ^ {- \frac {1}{\gamma}}.
$$

A <sub>c</sub>l<sub>earer</sub> <sub>v</sub>i<sub>ew</sub> <sub>o</sub>f th<sub>e</sub> th<sub>eorem</sub> i<sub>s</sub> th<sub>e</sub> f<sub>o</sub>ll<sub>ow</sub>i<sub>ng:</sub>

$$
\bar {F} _ {t} (x) = \mathbb {P} \left(X - t > x \mid X > t\right) \underset {t \to \tau} {\sim} \left(1 + \frac {\gamma x}{\sigma (t)}\right) ^ {- \frac {1}{\gamma}}.
$$

<sup>Thi</sup>s resu<sup>lt</sup> s<sup>h</sup>ows <sup>th</sup>a<sup>t th</sup>e excess over a <sup>th</sup>res<sup>h</sup>o<sup>ld</sup> t, wr<sup>itt</sup>en $X - t ,$ are likel<sub>y</sub> to follow a Generalized Pareto Distribution (GPD) with <sub>p</sub>arameters <sub>γ</sub>  <sub>σ</sub>. In fact<sub>,</sub> the GPD needs a third <sub>p</sub>arameter<sub>,</sub> the l<sub>oca</sub>ti<sub>on</sub> $\mu ,$ b<sub>u</sub>t it is n<sub>u</sub>ll in o<sub>u</sub>r case. Rather than fittin<sub>g</sub> an EVD to th<sub>e ex</sub>t<sub>reme va</sub>l<sub>ues o</sub>f $X ,$ th<sub>e</sub> POT <sub>app</sub>r<sub>oac</sub>h tri<sub>es</sub> t<sub>o</sub> fit <sub>a</sub> GPD t<sub>o</sub> th<sub>e</sub> excesses $X - t .$

In the case we <sub>g</sub>et estimates<sub>γ</sub>ˆ and <sub>σ</sub>ˆ (our method will be described in 3.4), the <sub>q</sub>uantile can be com<sub>p</sub>uted throu<sub>g</sub>h :

$$
z _ {q} \simeq t + \frac {\hat {\sigma}}{\hat {\gamma}} \left(\left(\frac {q n}{N _ {t}}\right) ^ {- \hat {\gamma}} - 1\right),\tag{1}
$$

where t is a “hi<sub>g</sub>h" threshold (details will be <sub>g</sub>iven in 4.3.3), <sub>q</sub> the d<sub>es</sub>i<sub>re</sub>d <sub>pro</sub>b<sub>a</sub>bilit<sub>y, n</sub> th<sub>e</sub> t<sub>o</sub>t<sub>a</sub>l <sub>num</sub>b<sub>er o</sub>f <sub>o</sub>b<sub>serva</sub>ti<sub>ons,</sub> $N _ { t }$ th<sub>e</sub> number of peaks i.e the number of $X _ { i } ~ { \mathrm { s . t . } } ~ X _ { i } > t$

S<sub>ome</sub> <sub>c</sub>l<sub>ass</sub>i<sub>ca</sub>l <sub>me</sub>th<sub>o</sub>d<sub>s</sub> <sub>can</sub> b<sub>e</sub> <sub>use</sub>d t<sub>o</sub> <sub>per</sub>f<sub>orm</sub> th<sub>e</sub> <sub>es</sub>ti<sub>ma</sub>ti<sub>on</sub> of<sub>γ</sub> and <sub>σ</sub>, as the Method of Moments (MOM) or the Probabilit<sub>y</sub> Wei<sub>g</sub>ted Moments (PWM) but the<sub>y</sub> are less eficient and robust than the maximum likelihood estimation [10] that we describe below.

## 3.4 Maximum likelihood estimation

3.4.1 Likelihood expression. The maximum likelihood estimati<sub>on rema</sub>i<sub>ns a na</sub>t<sub>ura</sub>l <sub>way</sub> t<sub>o eva</sub>l<sub>ua</sub>t<sub>e</sub> th<sub>e parame</sub>t<sub>ers</sub> th<sub>roug</sub>h <sub>o</sub>b<sub>se</sub>r<sub>va</sub>ti<sub>o</sub>n<sub>s.</sub> I $\mathbf { \dot { X } } _ { 1 } , \dots . . . X _ { n }$ <sub>are n</sub> i<sub>n</sub>d<sub>epen</sub>d<sub>en</sub>t <sub>rea</sub>li<sub>za</sub>ti<sub>ons o</sub>f th<sub>e</sub> random variable X which density (noted $f _ { \theta } )$ is parametrized by θ (<sub>p</sub>ossibl<sub>y</sub> a vector), the likelihood function is defined b<sub>y</sub>:

$$
\mathcal {L} \left(X _ {1}, \dots X _ {n}; \theta\right) = \prod_ {i = 1} ^ {n} f _ {\theta} (X _ {i}).
$$

It represents joint <sup>d</sup>ensity o<sup>f</sup> t<sup>h</sup>ese n o<sup>b</sup>servations. As $X _ { 1 } , \ldots$ $X _ { n }$ are fixed in our context, we try to find the parameter θ such th<sub>a</sub>t th<sub>e</sub> lik<sub>e</sub>lih<sub>oo</sub>d i<sub>s max</sub>i<sub>m</sub>i<sub>ze</sub>d<sub>.</sub> It <sub>means</sub> th<sub>a</sub>t <sub>we are</sub> l<sub>oo</sub>ki<sub>ng</sub> f<sub>or</sub> the value of θ which makes our observations the most probable. Practicall<sub>y</sub>, we work on the lo<sub>g</sub>-likelihood, so in our case (GPD fit) <sub>we</sub> h<sub>ave</sub> t<sub>o</sub> m<sub>a</sub>ximiz<sub>e</sub> :

$$
\log \mathcal {L} (\gamma , \sigma) = - N _ {t} \log \sigma - \left(1 + \frac {1}{\gamma}\right) \sum_ {i = 1} ^ {N _ {t}} \log \left(1 + \frac {\gamma}{\sigma} Y _ {i}\right),
$$

<sub>w</sub>h<sub>ere</sub> $Y _ { i } > 0$ <sub>are</sub> th<sub>e excesses o</sub>f $X _ { i }$ over $t ( Y _ { i } = X _ { i } - t$ f<sub>or</sub> $X _ { i } > t )$ Unfortunatel<sub>y,</sub> the o<sub>p</sub>timization must be done numericall<sub>y,</sub> im<sub>p</sub>l<sub>y</sub> in<sub>g</sub> the classical numerical issues. To <sub>p</sub>erform it<sub>,</sub> the <sub>p</sub>rocedure of Grimshaw [21] can be used.

In a strict GPD case (ifthe $Y _ { i }$ follow exactl<sub>y</sub> a GPD), the Maximum Likelihood Estimate (MLE) has some <sub>g</sub>ood conver<sub>g</sub>ence <sub>p</sub>ro<sub>p</sub>erties in com<sub>p</sub>arison to other estimates (MOM or PWM). It conver<sub>g</sub>es in di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on</sub> t<sub>o a</sub> G<sub>auss</sub>i<sub>an</sub> di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on w</sub>h<sub>en</sub> th<sub>e num</sub>b<sub>er o</sub>f <sub>pea</sub>k<sub>s</sub> $N _ { t }  \infty$ <sub>w</sub>h<sub>en</sub> $\gamma > - \frac { 1 } { 2 }$ (with a rate of consistenc<sub>y</sub> $\sqrt { N _ { t } } )$ <sub>an</sub>d i<sub>s</sub> <sub>supere</sub>fi<sub>c</sub>i<sub>en</sub>t <sub>w</sub>h<sub>en</sub> $- 1 < \gamma < - \frac { 1 } { 2 }$ with a rate of consistenc<sub>y</sub> $N _ { t } ^ { - \gamma }$

3.4.2 The Grimshaw’s trick. The trick of the Grimshaw’s procedure is to reduce the two variables o<sub>p</sub>timization <sub>p</sub>roblem to a sin<sub>g</sub>le <sub>va</sub>ri<sub>a</sub>bl<sub>e</sub> <sub>equa</sub>ti<sub>o</sub>n<sub>.</sub> L<sub>e</sub>t <sub>us</sub> <sub>w</sub>rit<sub>e</sub> $\ell ( \gamma , \sigma ) = \log { \mathcal { L } } ( \gamma , \sigma )$ <sub>.</sub> A<sub>s we</sub> fi<sub>n</sub>d <sub>an</sub> <sub>ex</sub>t<sub>remum</sub> <sub>o</sub>f $\ell ,$ <sub>we</sub> l<sub>oo</sub>k f<sub>or</sub> <sub>so</sub>l<sub>u</sub>ti<sub>ons</sub> <sub>o</sub>f th<sub>e</sub> <sub>sys</sub>t<sub>em</sub> $\nabla \ell ( \gamma , \sigma ) = 0 .$ G<sub>r</sub>i<sub>ms</sub>h<sub>aw</sub> h<sub>as</sub> <sub>s</sub>h<sub>own</sub> th<sub>a</sub>t if <sub>we</sub> <sub>ge</sub>t <sub>a</sub> <sub>so</sub>l<sub>u</sub>ti<sub>on</sub> $( \gamma ^ { * } , \sigma ^ { * } )$ <sub>o</sub>f thi<sub>s</sub> <sub>sys</sub> t<sub>em</sub> th<sub>en</sub> th<sub>e var</sub>i<sub>a</sub>bl<sub>e</sub> $x ^ { * } = \gamma ^ { * } / \sigma ^ { * }$ i<sub>s so</sub>l<sub>u</sub>ti<sub>on o</sub>f th<sub>e sca</sub>l<sub>ar equa</sub>ti<sub>on</sub> $u ( x ) v ( x ) = 1$ <sub>w</sub>h<sub>ere:</sub>

$$
u (x) = \frac {1}{N _ {t}} \sum_ {i = 1} ^ {N _ {t}} \frac {1}{1 + x Y _ {i}} v (x) = 1 + \frac {1}{N _ {t}} \sum_ {i = 1} ^ {N _ {t}} \log \left(1 + x Y _ {i}\right).
$$

M<sub>oreover,</sub> b<sub>y</sub> fi<sub>n</sub>di<sub>ng</sub> <sub>a</sub> <sub>so</sub>l<sub>u</sub>ti<sub>on</sub> $x ^ { * }$ of this e<sub>q</sub>uation<sub>,</sub> we can retrieve $\gamma ^ { * } = v \left( x ^ { * } \right) - 1$ <sub>an</sub>d $\sigma ^ { * } = \gamma ^ { * } / x ^ { * }$ <sub>.</sub> N<sub>ever</sub>th<sub>e</sub>l<sub>ess,</sub> th<sub>e so</sub>l<sub>u</sub>ti<sub>ons</sub> <sub>o</sub>f thi<sub>s equa</sub>ti<sub>on g</sub>i<sub>ve on</sub>l<sub>y poss</sub>ibl<sub>e can</sub>did<sub>a</sub>t<sub>es</sub> f<sub>or</sub> th<sub>e max</sub>i<sub>mum o</sub>f $\ell ,$ <sub>so</sub> <sub>we</sub> h<sub>ave</sub> t<sub>o</sub> <sub>ge</sub>t <sub>a</sub>ll th<sub>e</sub> <sub>roo</sub>t<sub>s,</sub> t<sub>o</sub> <sub>ca</sub>l<sub>cu</sub>l<sub>a</sub>t<sub>e</sub> th<sub>e</sub> <sub>correspon</sub>di<sub>ng</sub> likelihood and kee<sub>p</sub> the best tu<sub>p</sub>le (<sub>γ</sub>ˆ <sub>σ</sub>ˆ ) as our final estimates.

We have to <sub>p</sub>a<sub>y</sub> attention to how this numerical root search is done. In fact, the values 1 + xY must be strictly positives. As the $Y _ { i }$ <sub>are</sub> <sub>pos</sub>iti<sub>ve,</sub> <sub>we</sub> <sub>mus</sub>t fi<sub>n</sub>d $x ^ { * }$ on $\left( - \frac { 1 } { \Upsilon ^ { M } } , + \infty \right)$ <sub>w</sub>h<sub>ere</sub> $\mathbf { Y } ^ { M } = \operatorname* { m a x } Y _ { i } .$ G<sub>r</sub>i<sub>ms</sub>h<sub>aw ca</sub>l<sub>cu</sub>l<sub>a</sub>t<sub>es a</sub>l<sub>so an upper-</sub>b<sub>oun</sub>d $x _ { \mathrm { m a x } } ^ { * }$ f<sub>or</sub> thi<sub>s roo</sub>t <sub>searc</sub>h<sub>:</sub>

$$
x _ {\mathrm{max}} ^ {*} = 2 \frac {\overline {{\mathbf {Y}}} - \mathbf {Y} ^ {m}}{(\mathbf {Y} ^ {m}) ^ {2}},
$$

<sub>w</sub>h<sub>ere</sub> ${ \bf Y } ^ { m } =$ min $Y _ { i }$ <sub>an</sub>d $\overline { { \mathbf { Y } } }$ i<sub>s</sub> th<sub>e mean o</sub>f th<sub>e</sub> $Y _ { i }$ <sub>.</sub> Fi<sub>na</sub>ll<sub>y,</sub> th<sub>e num</sub>b<sub>er</sub> <sub>o</sub>f <sub>roo</sub>t<sub>s</sub> i<sub>s no</sub>t k<sub>nown an</sub>d 0 i<sub>s a</sub>l<sub>ways a so</sub>l<sub>u</sub>ti<sub>on so</sub> th<sub>e</sub> i<sub>mp</sub>l<sub>emen</sub>t<sub>a</sub> ti<sub>on mus</sub>t fi<sub>n</sub>d <sub>a</sub>ll th<sub>e so</sub>l<sub>u</sub>ti<sub>ons an</sub>d <sub>p</sub>i<sub>c</sub>k <sub>up</sub> th<sub>ose w</sub>hi<sub>c</sub>h <sub>max</sub>i<sub>m</sub>i<sub>zes</sub> th<sub>e</sub> lik<sub>e</sub>lih<sub>oo</sub>d<sub>.</sub>

## 4 OUR CONTRIBUTION

The extreme value theor<sub>y,</sub> throu<sub>g</sub>h the POT a<sub>pp</sub>roach<sub>,</sub> <sub>g</sub>ives us a wa<sub>y</sub> to est<sup>i</sup>mate $z _ { q }$ <sub>suc</sub>h th<sub>a</sub>t $\mathbb { P } ( X > z _ { q } ) < q$ w<sup>i</sup>t<sup>h</sup>out an<sub>y</sub> stron<sub>g</sub> assumption on t<sup>h</sup>e <sup>d</sup>istri<sup>b</sup>ution o<sup>f</sup>X an<sup>d</sup> wit<sup>h</sup>out any c<sup>l</sup>ear <sup>k</sup>now<sup>l</sup>e<sup>d</sup>ge <sub>a</sub>b<sub>ou</sub>t it<sub>s</sub> di<sub>s</sub>trib<sub>u</sub>ti<sub>o</sub>n<sub>.</sub>

In this section we use this result to build a streamin<sub>g</sub> outlier detector. First <sub>w</sub>e <sub>p</sub>resent the initialization ste<sub>p</sub> <sub>w</sub>hich com<sub>pu</sub>tes <sub>an</sub> th<sub>res</sub>h<sub>o</sub>ld $z _ { q }$ f<sub>rom n o</sub>b<sub>serva</sub>ti<sub>ons</sub> $X _ { 1 } , \dots X _ { n }$ <sub>.</sub> Th<sub>en, we</sub> d<sub>e</sub>t<sub>a</sub>il our two streamin<sub>g</sub> al<sub>g</sub>orithms which u<sub>p</sub>date $z _ { q }$ <sub>w</sub>ith th<sub>e</sub> i<sub>ncom</sub> in<sub>g</sub> d<sub>a</sub>t<sub>a a</sub>nd <sub>use</sub> it <sub>as a</sub> d<sub>ec</sub>i<sub>s</sub>i<sub>o</sub>n b<sub>ou</sub>nd<sub>.</sub> W<sub>e p</sub>r<sub>opose</sub> SPOT <sub>w</sub>hi<sub>c</sub>h <sub>wo</sub>rk<sub>s</sub> in <sub>s</sub>t<sub>a</sub>ti<sub>o</sub>n<sub>a</sub>r<sub>y cases, a</sub>nd DSPOT <sub>w</sub>hi<sub>c</sub>h t<sub>a</sub>k<sub>es</sub> int<sub>o accou</sub>nt <sub>a</sub> d<sub>r</sub>ift <sub>componen</sub>t<sub>.</sub> Fi<sub>na</sub>ll<sub>y we g</sub>i<sub>ve some</sub> th<sub>eore</sub>ti<sub>ca</sub>l <sub>an</sub>d t<sub>ec</sub>h<sub>n</sub>i<sub>ca</sub>l i<sub>mprovemen</sub>t<sub>s ma</sub>ki<sub>ng our</sub> b<sub>oun</sub>d <sub>up</sub>d<sub>a</sub>t<sub>e</sub> f<sub>as</sub>t <sub>an</sub>d <sub>s</sub>t<sub>ur</sub>d<sub>y.</sub>

## 4.1 Initialization step

L<sub>e</sub>t <sub>us sum up</sub> th<sub>e</sub> b<sub>as</sub>i<sub>c</sub> id<sub>ea o</sub>f <sub>our a</sub>l<sub>gor</sub>ith<sub>m.</sub> W<sub>e</sub> h<sub>ave n o</sub>b<sub>serva</sub> tions $X _ { 1 } , \dots X _ { n }$ <sub>, an</sub>d <sub>we</sub> h<sub>ave</sub> fi<sub>xe</sub>d <sub>a r</sub>i<sub>s</sub>k <sub>q.</sub> Th<sub>e goa</sub>l i<sub>s</sub> t<sub>o compu</sub>t<sub>e</sub> <sub>a</sub> fi<sub>rs</sub>t th<sub>res</sub>h<sub>o</sub>ld $z _ { q }$ verif<sub>y</sub>in<sub>g</sub> $\mathbb { P } ( X > z _ { q } ) < q .$ Th<sub>e</sub> fi<sub>gure</sub> 3 <sub>s</sub>h<sub>ows</sub> what we do on this initial batch (calibration). The idea is to set a hi<sub>g</sub>h threshold t (e.<sub>g</sub>. a hi<sub>g</sub>h em<sub>p</sub>irical <sub>q</sub>uantile <sub>p</sub>racticall<sub>y</sub>), retrieve the peaks (the excesses over t) and fit a GPD (Generalized Pareto Distribution) to them. So that we infer the distribution of th<sub>e</sub> <sub>ex</sub>t<sub>reme</sub> <sub>va</sub>l<sub>ues</sub> <sub>an</sub>d <sub>we</sub> <sub>can</sub> <sub>compu</sub>t<sub>e</sub> th<sub>e</sub> th<sub>res</sub>h<sub>o</sub>ld $z _ { q }$

Thi<sub>s</sub> initi<sub>a</sub>liz<sub>a</sub>ti<sub>o</sub>n <sub>s</sub>t<sub>ep</sub> i<sub>s</sub> <sub>su</sub>mm<sub>a</sub>riz<sub>e</sub>d in th<sub>e</sub> <sub>a</sub>l<sub>go</sub>rithm 1<sub>.</sub> Th<sub>e</sub> c<sup>h</sup>o<sup>i</sup>ce o<sup>f</sup>t w<sup>ill b</sup>e <sup>di</sup>scusse<sup>d i</sup>n <sup>4</sup>.<sup>3</sup>.<sup>3</sup>. <sup>Th</sup>e se<sup>t</sup> $\mathbf { Y } _ { t }$ is the peaks set where we s<sup>t</sup>ore <sup>th</sup>e o<sup>b</sup>serve<sup>d</sup> excesses over t. <sup>Th</sup>e <sup>GPD fit i</sup>s per<sup>f</sup>orme<sup>d</sup> with the Grimshaw trick (we detail our likelihood o<sub>p</sub>timization in 4.3.2) and then we can com<sub>p</sub>ute $z _ { q }$ <sub>w</sub>ith e<sub>qu</sub>ation 1.

```txt
Algorithm 1 POT (Peaks-over-Threshold)
1: procedure POT(X₁, . . . Xₙ, q)
2: t ← SETINITIALTHRESHOLD(X₁, . . . Xₙ)
3: Yₜ ← {Xᵢ - t | Xᵢ > t}
4: γ̂, σ̂ ← GRIMSHAW(Yₜ)
5: z_q ← CALCTHRESHOLD(q, γ̂, σ̂, n, Nₜ, t)
6: return z_q, t
7: end procedure
```

## 4.2 Finding anomalies in a stream

Th<sub>e</sub> POT <sub>p</sub>rimiti<sub>ve</sub> r<sub>e</sub>t<sub>u</sub>rn<sub>s</sub> <sub>a</sub> thr<sub>es</sub>h<sub>o</sub>ld $z _ { q }$ <sub>w</sub>hi<sub>c</sub>h <sub>we</sub> <sub>use</sub> t<sub>o</sub> d<sub>e</sub>fi<sub>ne</sub> <sub>a</sub> "normalit<sub>y</sub> bound" (fi<sub>g</sub>ure 3).

In our streamin<sub>g</sub> al<sub>g</sub>orithms the POT <sub>p</sub>rimitive (al<sub>g</sub>orithm 1) is <sub>use</sub>d <sub>as</sub> <sub>a</sub>n initi<sub>a</sub>liz<sub>a</sub>ti<sub>o</sub>n <sub>s</sub>t<sub>ep.</sub>

The POT primitive may be seen as a training step but this is partly <sub>wrong</sub> b<sub>ecause</sub> th<sub>e</sub> i<sub>n</sub>iti<sub>a</sub>l b<sub>a</sub>t<sub>c</sub>h $X _ { 1 } , \dots X _ { n }$ i<sub>s no</sub>t l<sub>a</sub>b<sub>e</sub>l<sub>e</sub>d <sub>an</sub>d i<sub>s no</sub>t considered as a <sub>g</sub>round truth in our al<sub>g</sub>orithm. The initialization is more a calibration step. Our streaming anomaly detector uses the <sub>nex</sub>t <sub>o</sub>b<sub>serva</sub>ti<sub>ons</sub> t<sub>o</sub> b<sub>o</sub>th d<sub>e</sub>t<sub>ec</sub>t <sub>anoma</sub>li<sub>es an</sub>d <sub>re</sub>fi<sub>ne</sub> th<sub>e anoma</sub>l<sub>y</sub> th<sub>res</sub>h<sub>o</sub>ld $z _ { q } .$

4.2.1 Stationary case. The way how the POT estimate is built i<sub>s rea</sub>ll<sub>y s</sub>t<sub>ream-rea</sub>d<sub>y.</sub> A<sub>s we</sub> d<sub>o no</sub>t h<sub>ave</sub> t<sub>o s</sub>t<sub>ore</sub> th<sub>e w</sub>h<sub>o</sub>l<sub>e</sub> ti<sub>me</sub> series (onl<sub>y</sub> the <sub>p</sub>eaks), it re<sub>q</sub>uires low memor<sub>y</sub> so we can use it in <sub>a s</sub>t<sub>ream.</sub> H<sub>owever,</sub> th<sub>e s</sub>t<sub>ream mus</sub>t <sub>con</sub>t<sub>a</sub>i<sub>n va</sub>l<sub>ues</sub> f<sub>rom</sub> th<sub>e same</sub> distribution, so this distribution cannot been time-de<sub>p</sub>endent (what we call stationary). In case of time-dependency, we will show that our al<sub>g</sub>orithm can be ada<sub>p</sub>ted to driftin<sub>g</sub> cases (see 4.2.2).

The <sub>p</sub>rinci<sub>p</sub>le ofthe SPOT al<sub>g</sub>orithm is the followin<sub>g</sub> : we want to d<sub>e</sub>t<sub>ec</sub>t <sub>a</sub>b<sub>norma</sub>l <sub>even</sub>t<sub>s</sub> i<sub>n a s</sub>t<sub>ream</sub> $( X _ { i } ) _ { i > 0 }$ in a blind wa<sub>y</sub> (without knowled<sub>g</sub>e about the distribution). Firstl<sub>y</sub>, we <sub>p</sub>erform a POT estimate on the <sub>n</sub> first values (<sub>n</sub> ∼ 1000) and we <sub>g</sub>et an initial threshold $z _ { q }$ (initialization). Then for all the next observed values we can fla<sub>g</sub> the events or u<sub>p</sub>date the threshold (see fi<sub>g</sub>ure 3). If a value <sub>excee</sub>d<sub>s our</sub> th<sub>res</sub>h<sub>o</sub>ld $z _ { q }$ then we consider it as abnormal (we can retrieve this anomaly in a list A). The anomalies are not taken into <sub>accoun</sub>t f<sub>or</sub> th<sub>e</sub> <sub>mo</sub>d<sub>e</sub>l <sub>up</sub>d<sub>a</sub>t<sub>e.</sub> I<sub>n</sub> th<sub>e</sub> <sub>o</sub>th<sub>er</sub> <sub>cases,</sub> <sub>e</sub>ith<sub>er</sub> $X _ { i }$ <sup>i</sup>s <sub>g</sub>reater than the initial threshold (<sub>p</sub>eak case) either it is a “common" value (normal case). In the <sub>p</sub>eak case, we add the excess to the <sub>p</sub>eaks set <sub>an</sub>d <sub>we up</sub>d<sub>a</sub>t<sub>e</sub> th<sub>e</sub> th<sub>res</sub>h<sub>o</sub>ld $z _ { q }$

I<sub>n</sub> thi<sub>s a</sub>l<sub>gor</sub>ith<sub>m we per</sub>f<sub>orm</sub> th<sub>e max</sub>i<sub>mum num</sub>b<sub>er o</sub>f th<sub>res</sub>h<sub>o</sub>ld <sub>up</sub>d<sub>a</sub>t<sub>es</sub> b<sub>u</sub>t it i<sub>s poss</sub>ibl<sub>e</sub> t<sub>o</sub> d<sub>o</sub> it <sub>o</sub>f<sub>-</sub>li<sub>ne a</sub>t fi<sub>xe</sub>d ti<sub>me</sub> i<sub>n</sub>t<sub>erva</sub>l<sub>.</sub> Of <sub>course we</sub> ill<sub>us</sub>t<sub>ra</sub>t<sub>e</sub> th<sub>e pr</sub>i<sub>nc</sub>i<sub>p</sub>l<sub>e on</sub>l<sub>y w</sub>ith <sub>upper-</sub>b<sub>oun</sub>d th<sub>res</sub>h<sub>o</sub>ld<sub>s</sub> b<sub>u</sub>t th<sub>e me</sub>th<sub>o</sub>d i<sub>s</sub> th<sub>e same</sub> f<sub>or</sub> l<sub>ower-</sub>b<sub>oun</sub>d <sub>ones an</sub>d <sub>we can even</sub> combine both (<sub>p</sub>erformances will be <sub>p</sub>resented in 5.4).

```txt
Algorithm 2 SPOT (Streaming POT)
1: procedure SPOT((Xi)_{i>0}, n, q)
2:    A ← ∅    ▷ set of the anomalies
3:    z_q, t ← POT(X_1, ... X_n, q)
4:    k ← n
5:    for i > n do
6:    if X_i > z_q then    ▷ anomaly case
7:    Add (i, X_i) in A
8:    else if X_i > t then    ▷ real peak case
9:    Y_i ← X_i - t
10:    Add Y_i in Y_t
11:    N_t ← N_t + 1
12:    k ← k + 1
13:    γ̂, σ ← GRIMSHAW(Y_t)
14:    z_q ← CALCTHRESHOLD(q, γ̂, σ̂, k, N_t, t)
15:    else    ▷ normal case
16:    k ← k + 1
17:    end if
18:    end for
19: end procedure
```

![](images/9f43bab7a1c645d500092c19e5a21b19cc5f56fb3c954d4a6230524b03e5d9d3.jpg)

4.2.2 Drifting case. SPOT assumes that the distribution of the $X _ { i }$ does not chan<sub>g</sub>e over time b<sub>u</sub>t it mi<sub>g</sub>ht be restrictive. For instance<sub>,</sub> <sub>a</sub> <sub>m</sub>id<sub>-</sub>t<sub>erm</sub> <sub>seasona</sub>lit<sub>y</sub> <sub>canno</sub>t b<sub>e</sub> t<sub>a</sub>k<sub>en</sub> i<sub>n</sub>t<sub>o</sub> <sub>accoun</sub>t<sub>,</sub> <sub>ma</sub>ki<sub>ng</sub> l<sub>o-</sub> <sub>ca</sub>l <sub>pea</sub>k<sub>s un</sub>d<sub>e</sub>t<sub>ec</sub>t<sub>a</sub>bl<sub>e.</sub> I<sub>n</sub> thi<sub>s sec</sub>ti<sub>on we overcome</sub> thi<sub>s</sub> i<sub>ssue</sub> b<sub>y</sub> modelin<sub>g</sub> an avera<sub>g</sub>e local behavior and a<sub>pp</sub>l<sub>y</sub>in<sub>g</sub> SPOT on relative g<sup>a</sup>p<sup>s.</sup>

We <sub>p</sub>ro<sub>p</sub>ose Drift SPOT (DSPOT) which makes SPOT run not <sub>on</sub> th<sub>e a</sub>b<sub>so</sub>l<sub>u</sub>t<sub>e va</sub>l<sub>ues</sub> $X _ { i }$ b<sub>u</sub>t <sub>on</sub> th<sub>e re</sub>l<sub>a</sub>ti<sub>ve ones.</sub> W<sub>e use</sub> th<sub>e</sub> <sub>var</sub>i<sub>a</sub>bl<sub>e c</sub>h<sub>ange</sub> $X _ { i } ^ { \prime } = X _ { i } - M _ { i }$ <sub>w</sub>h<sub>ere</sub> $M _ { i }$ <sub>mo</sub>d<sub>e</sub>l<sub>s</sub> th<sub>e</sub> l<sub>oca</sub>l b<sub>e</sub>h<sub>av</sub>i<sub>or</sub> at time i (see fi<sub>g</sub>ure 4). In our im<sub>p</sub>lementation we used a movin<sub>g</sub> <sup>avera</sup>g<sup>e</sup> $M _ { i } \ = \ ( 1 / d ) \cdot \sum _ { k = 1 } ^ { d } X _ { i - k } ^ { * }$ <sub>w</sub>ith $X _ { i - 1 } ^ { * } , \ldots . X _ { i - d } ^ { * }$ the last d "normal" observations (so d is a window <sub>p</sub>arameter). In this new <sub>con</sub>t<sub>ex</sub>t <sub>we</sub> <sub>assume</sub> th<sub>a</sub>t th<sub>e</sub> l<sub>oca</sub>l <sub>var</sub>i<sub>a</sub>ti<sub>ons</sub> $X _ { i } ^ { \prime }$ <sub>come</sub> f<sub>rom</sub> <sub>a</sub> <sub>same</sub> stationar<sub>y</sub> distribution (the h<sub>yp</sub>othesis assumed for $X _ { i }$ i<sub>n</sub> SPOT i<sub>s</sub> <sub>now assume</sub>d f<sub>or</sub> $X _ { i } ^ { \prime } ) .$

This variant uses an additional parameter d, which can be viewed as a window size. The distinctive features of this window (noted $W ^ { * } )$ <sub>are</sub> th<sub>e</sub> f<sub>o</sub>ll<sub>ow</sub>i<sub>ng:</sub> it <sub>m</sub>i<sub>g</sub>ht b<sub>e non con</sub>ti<sub>nuous an</sub>d it d<sub>oes no</sub>t <sub>con</sub>t<sub>a</sub>i<sub>n a</sub>b<sub>norma</sub>l <sub>va</sub>l<sub>ues.</sub>

![](images/367757d3e395c4750f1c0a0b4a6af46fa8f037315dd3272d9198cd7892354df5.jpg)  
Figure 4: Anomaly detection with drift

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 3 DSPOT (Streaming POT with drift)

1: procedure DSPOT((Xi)_{i&gt;0}, n, d, q)
2:    A ← ∅
3:    W* ← [X₁, ... X_d]
4:    M_{d+1} = \overline{W*}
5:    for i ∈ [[d + 1, d + n]] do
6:    X_i' = X_i - M_i
7:    W* ← [X_{i-d+1}, ... X_i]
8:    M_{i+1} ← \overline{W*}
9:    end for
10:    z_q, t ← POT(X_{d+1}', ... X_{d+n}', q)
11:    k ← n
12:    for i &gt; d + n do
13:    X_i' = X_i - M_i
14:    if X_i' &gt; z_q then
15:    Add (i, X_i) in A
16:    M_{i+1} ← M_i
17:    else if X_i' &gt; t then
18:    Y_i ← X_i' - t
19:    Add Y_i in Y_t
20:    N_t ← N_t + 1
21:    k ← k + 1
22:    $\hat{\gamma}$, $\hat{\sigma}$ ← GRIMSHAW(Y_t)
23:    z_q ← CALCTHRESHOLD(q, $\hat{\gamma}$, $\hat{\sigma}$, k, N_t, t)
24:    W* ← W*[1:] ∪ X_i
25:    M_{i+1} ← $\overline{W*}$
26:    else
27:    k ← k + 1
28:    W* ← W*[1:] ∪ X_i
29:    M_{i+1} ← $\overline{W*}$
30:    end if
31:    end for
32: end procedure
</div>

Th<sub>e a</sub>l<sub>gor</sub>ith<sub>m</sub> 3 <sub>s</sub>h<sub>ows our me</sub>th<sub>o</sub>d t<sub>o cap</sub>t<sub>ure</sub> th<sub>e</sub> l<sub>oca</sub>l <sub>mo</sub>d<sub>e</sub>l <sub>an</sub>d <sub>pe</sub>rf<sub>o</sub>rm SPOT thr<sub>es</sub>h<sub>o</sub>ldin<sub>g</sub> <sub>o</sub>n l<sub>oca</sub>l <sub>va</sub>ri<sub>a</sub>ti<sub>o</sub>n<sub>s.</sub> It <sub>co</sub>nt<sub>a</sub>in<sub>s</sub> <sub>so</sub>m<sub>e</sub> additional ste<sub>p</sub>s so as to com<sub>p</sub>ute variable chan<sub>g</sub>es. For these sta<sub>g</sub>es<sub>,</sub> we <sub>p</sub>rinci<sub>p</sub>all<sub>y</sub> use a slidin<sub>g</sub> windows over normal observations $W ^ { * }$ (lines 3, 7, 24 and 28) in order to calculate a local normal behavior $M _ { i }$ (lines 4, 8, 25 and 29) throu<sub>g</sub>h avera<sub>g</sub>in<sub>g</sub>. We lo<sub>g</sub>icall<sub>y</sub> u<sub>p</sub>date the local behavior onl<sub>y</sub> in normal or <sub>p</sub>eak cases (lines 25 and 29).

W<sub>e can re</sub>t<sub>r</sub>i<sub>eve sequen</sub>ti<sub>a</sub>ll<sub>y</sub> th<sub>e</sub> “<sub>rea</sub>l" <sub>ex</sub>t<sub>reme quan</sub>til<sub>es</sub> b<sub>y</sub> a<sup>dd</sup>ing M to t<sup>h</sup>e ca<sup>l</sup>cu<sup>l</sup>ate<sup>d</sup> $z _ { q } .$ <sub>.</sub> S<sub>uc</sub>h <sub>a c</sub>h<sub>o</sub>i<sub>ce</sub> t<sub>o mo</sub>d<sub>e</sub>l th<sub>e</sub> l<sub>oca</sub>l beha<sub>v</sub>ior is a <sub>v</sub>er<sub>y</sub> eficient <sub>w</sub>a<sub>y</sub> to ada<sub>p</sub>t SPOT to driftin<sub>g</sub> contexts. As mentioned in the <sub>p</sub>revio<sub>u</sub>s <sub>p</sub>ara<sub>g</sub>ra<sub>p</sub>h<sub>,</sub> DSPOT can be ada<sub>p</sub>ted to <sub>compu</sub>t<sub>e</sub> <sub>upper</sub> <sub>an</sub>d l<sub>ower</sub> b<sub>oun</sub>d<sub>s.</sub>

## 4.3 Numerical optimization

The streamin<sub>g</sub> context re<sub>q</sub>uests fast and resilient al<sub>g</sub>orithms. In this <sub>p</sub>art<sub>,</sub> we o<sub>p</sub>timize the GPD fit b<sub>y</sub> reducin<sub>g</sub> the search of o<sub>p</sub>timal <sub>p</sub>arameters and makin<sub>g</sub> it more robust to common numerical stabilit<sub>y</sub> <sub>p</sub>roblems (diver<sub>g</sub>ence, absurd values). The <sub>p</sub>ro<sub>p</sub>osition 4.1 <sub>g</sub>ives a <sub>g</sub>eneral result for EVT<sub>,</sub> im<sub>p</sub>rovin<sub>g</sub> the Grimshaw’s trick. In 4.3.2<sub>,</sub> <sub>we</sub> d<sub>e</sub>t<sub>a</sub>il h<sub>ow</sub> <sub>we</sub> <sub>per</sub>f<sub>orm</sub> th<sub>e</sub> lik<sub>e</sub>lih<sub>oo</sub>d <sub>op</sub>ti<sub>m</sub>i<sub>za</sub>ti<sub>on</sub> <sub>an</sub>d fi<sub>na</sub>ll<sub>y</sub> we g<sup>i</sup>ve some <sup>d</sup>e<sup>t</sup>a<sup>il</sup>s a<sup>b</sup>ou<sup>t</sup> <sup>th</sup>e <sup>i</sup>n<sup>iti</sup>a<sup>l</sup> <sup>th</sup>res<sup>h</sup>o<sup>ld</sup> t.

4.3.1 Reduction ofthe optimal parameters search. As we have <sub>seen</sub> i<sub>n sec</sub>ti<sub>on</sub> 3<sub>.</sub>4<sub>.</sub>2<sub>,</sub> th<sub>e</sub> G<sub>r</sub>i<sub>ms</sub>h<sub>aw</sub>’<sub>s me</sub>th<sub>o</sub>d f<sub>or</sub> th<sub>e max</sub>i<sub>mum</sub> lik<sub>e</sub>lih<sub>oo</sub>d <sub>es</sub>ti<sub>ma</sub>ti<sub>on requ</sub>i<sub>res a numer</sub>i<sub>ca</sub>l <sub>roo</sub>t <sub>searc</sub>h i<sub>n a</sub> b<sub>oun</sub>d<sub>e</sub>d i<sub>n</sub>t<sub>erva</sub>l<sub>.</sub> I<sub>n</sub> thi<sub>s</sub> <sub>paragrap</sub>h <sub>we</sub> <sub>s</sub>h<sub>ow</sub> th<sub>a</sub>t <sub>we</sub> <sub>can</sub> <sub>re</sub>d<sub>uce</sub> thi<sub>s</sub> i<sub>n</sub>t<sub>erva</sub>l<sub>.</sub>

Gatherin<sub>g</sub> the followin<sub>g</sub> result and the <sub>p</sub>revious bounds (section $3 . 4 . 2 )$ <sub>,</sub> th<sub>e poss</sub>ibl<sub>e so</sub>l<sub>u</sub>ti<sub>ons o</sub>f $u ( x ) v ( x ) = 1$ <sub>s</sub>t<sub>an</sub>d i<sub>n</sub> th<sub>e</sub> t<sub>wo</sub> i<sub>n</sub>t<sub>erva</sub>l<sub>s</sub>

$$
\left(- \frac {1}{\mathbf {Y} ^ {M}}, 0 \right] \text {   and   } \left[ 2 \frac {\overline {{\mathbf {Y}}} - \mathbf {Y} ^ {m}}{\overline {{\mathbf {Y}}} \mathbf {Y} ^ {m}}, 2 \frac {\overline {{\mathbf {Y}}} - \mathbf {Y} ^ {m}}{(\mathbf {Y} ^ {m}) ^ {2}} \right].
$$

Proposition 4.1. $H x ^ { * }$ is a solution $o f u ( x ) v ( x ) = 1$

$$
x ^ {*} \leq 0 \quad o r \quad x ^ {*} \geq 2 \frac {\overline {{\mathbf {Y}}} - \mathbf {Y} ^ {m}}{\overline {{\mathbf {Y}}} \mathbf {Y} ^ {m}}.
$$

Proof<sub>.</sub> Si<sub>nce</sub> $\begin{array} { r } { \forall x > - 1 , \log ( 1 + x ) \geq \frac { 2 x } { 2 + x } = 2 - \frac { 4 } { 2 + x } } \end{array}$

$$
v (x) \geq 1 + \frac {1}{N _ {t}} \sum_ {i = 1} ^ {N _ {t}} \left(2 - \frac {4}{2 + x Y _ {i}}\right) \geq 3 - \frac {4}{2 + x \mathbf {Y} ^ {m}}.
$$

Then a<sub>pp</sub>l<sub>y</sub>in<sub>g</sub> Jensen’s ine<sub>q</sub>ualit<sub>y</sub> on the convex function $x \mapsto { \textstyle { \frac { 1 } { 1 + x } } }$ <sup>we</sup> g<sup>et</sup> <sup>:</sup>

$$
u (x) \geq \frac {1}{1 + x \overline {{\mathbf {Y}}}},
$$

<sub>so</sub> th<sub>a</sub>t

$$
u (x) v (x) \geq \left(3 - \frac {4}{2 + x \mathbf {Y} ^ {m}}\right) \left(\frac {1}{1 + x \overline {{\mathbf {Y}}}}\right).
$$

If $x ^ { * }$ is a solution of the e<sub>q</sub>uation $u ( x ) v ( x ) = 1 ;$ <sub>, we mus</sub>t h<sub>ave</sub>

$$
1 \geq \left(3 - \frac {4}{2 + x ^ {*} \mathbf {Y} ^ {m}}\right) \left(\frac {1}{1 + x ^ {*} \overline {{\mathbf {Y}}}}\right).
$$

Sim<sub>p</sub>lif<sub>y</sub>in<sub>g</sub> this ine<sub>q</sub>ualit<sub>y,</sub> we <sub>g</sub>et

$$
x ^ {*} \left(x ^ {*} \mathbf {Y} ^ {m} \overline {{\mathbf {Y}}} - 2 \left(\overline {{\mathbf {Y}}} - \mathbf {Y} ^ {m}\right)\right) \geq 0.
$$

And a sim<sub>p</sub>le si<sub>g</sub>n stud<sub>y</sub> <sub>g</sub>ives the result.

4.3.2 How can we maximize the likelihood function? Finding the <sub>max</sub>i<sub>mum</sub> <sub>o</sub>f th<sub>e</sub> lik<sub>e</sub>lih<sub>oo</sub>d b<sub>o</sub>il<sub>s</sub> d<sub>own</sub> t<sub>o</sub> <sub>app</sub>l<sub>y</sub> <sub>a</sub> <sub>roo</sub>t <sub>searc</sub>h<sub>.</sub> B<sub>u</sub>t thi<sub>s</sub> i<sub>s no</sub>t <sub>a</sub> t<sub>r</sub>i<sub>v</sub>i<sub>a</sub>l t<sub>as</sub>k<sub>: we</sub> d<sub>o no</sub>t k<sub>now</sub> th<sub>e num</sub>b<sub>er o</sub>f <sub>roo</sub>t<sub>s an</sub>d <sub>a</sub>ll th<sub>e roo</sub>t<sub>s are po</sub>t<sub>en</sub>ti<sub>a</sub>l <sub>can</sub>did<sub>a</sub>t<sub>es</sub> t<sub>o max</sub>i<sub>m</sub>i<sub>ze</sub> thi<sub>s</sub> f<sub>unc</sub>ti<sub>on.</sub>

In [21], Grimshaw <sub>g</sub>ives an anal<sub>y</sub>tic-based routine usin<sub>g</sub> rootfi<sub>n</sub>di<sub>ng a</sub>l<sub>gor</sub>ith<sub>m</sub> i<sub>s g</sub>i<sub>ven</sub> h<sub>owever</sub> th<sub>e nee</sub>d<sub>e</sub>d <sub>con</sub>diti<sub>on</sub> $f ( a ) f ( b ) <$ 0 is not em<sub>p</sub>hasized leadin<sub>g</sub> to uncertain results. For this reason we d<sub>ec</sub>id<sub>e</sub> t<sub>o use ano</sub>th<sub>er me</sub>th<sub>o</sub>d t<sub>o</sub> fi<sub>n</sub>d th<sub>ese roo</sub>t<sub>s.</sub>

In our im<sub>p</sub>lementation<sub>,</sub> we set a ver<sub>y</sub> small $\epsilon > 0 ( \sim 1 0 ^ { - 8 } )$ <sub>an</sub>d <sub>we</sub> l<sub>oo</sub>k f<sub>or</sub> th<sub>e roo</sub>t<sub>s o</sub>f th<sub>e</sub> f<sub>unc</sub>ti<sub>on w</sub> $: x \mapsto u ( x ) v ( x ) - 1$ i<sub>n</sub> b<sub>o</sub>th i<sub>n</sub>t<sub>erva</sub>l<sub>s</sub>

$$
\left[ - \frac {1}{\mathbf {Y} ^ {M}} + \epsilon , - \epsilon \right] \mathrm{and} \left[ 2 \frac {\overline {{\mathbf {Y}}} - \mathbf {Y} ^ {m}}{\overline {{\mathbf {Y}}} \mathbf {Y} ^ {m}}, 2 \frac {\overline {{\mathbf {Y}}} - \mathbf {Y} ^ {m}}{(\mathbf {Y} ^ {m}) ^ {2}} \right].
$$

Th<sub>e</sub> <sub>rea</sub>l <sub>ϵ</sub> i<sub>s</sub> <sub>use</sub>d t<sub>o</sub> <sub>avo</sub>id b<sub>o</sub>th <sub>cases</sub> $\begin{array} { r } { x = \frac { 1 } { \mathbf { V } ^ { M } } } \end{array}$ (where <sub>w</sub> is not defined) and $x = 0$ (which is alwa<sub>y</sub>s a solution).

Man<sub>y</sub> methods exist to find multi<sub>p</sub>le roots of <sub>p</sub>ol<sub>y</sub>nomials (such as Sturm method) but not for the <sub>g</sub>eneral case of scalar functions. F<sub>ur</sub>th<sub>ermore,</sub> fi<sub>n</sub>di<sub>ng a roo</sub>t <sub>nee</sub>d<sub>s a s</sub>i<sub>gn c</sub>h<sub>ange w</sub>hi<sub>c</sub>h <sub>may</sub> b<sub>e</sub> dif<sub>-</sub> fi<sub>cu</sub>lt t<sub>o</sub> d<sub>e</sub>t<sub>ec</sub>t<sub>.</sub> Th<sub>us we</sub> h<sub>ave re</sub>d<sub>uce</sub>d <sub>our roo</sub>t <sub>searc</sub>h t<sub>o a</sub> f<sub>unc</sub>ti<sub>on</sub> minimiz<sub>a</sub>ti<sub>o</sub>n <sub>w</sub>hi<sub>c</sub>h r<sub>equ</sub>ir<sub>es</sub> l<sub>ess</sub> <sub>assu</sub>m<sub>p</sub>ti<sub>o</sub>n<sub>s.</sub>

T<sub>o</sub> fi<sub>n</sub>d th<sub>e zeros o</sub>f <sub>w we so</sub>l<sub>ve numer</sub>i<sub>ca</sub>ll<sub>y</sub> th<sub>e</sub> f<sub>o</sub>ll<sub>ow</sub>i<sub>ng op</sub>ti<sub>-</sub> mization <sub>p</sub>roblem in both intervals (that we note I):

$$
\min _ {x _ {1}, \ldots x _ {k} \in I} \sum_ {i = 1} ^ {k} w (x _ {k}) ^ {2}.
$$

The minimization can be done with a classical al<sub>g</sub>orithm (e.<sub>g</sub>. L-BFGS-B [12]) startin<sub>g</sub> with k <sub>p</sub>oints $x _ { 1 } ^ { 0 } , . . . x _ { k } ^ { 0 } \ : ( k \simeq 1 0 )$ di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>t<sub>e</sub>d over I. We use t<sup>h</sup>is proce<sup>d</sup>ure <sup>f</sup>or t<sup>h</sup>ree reasons: t<sup>h</sup>e optima<sup>l</sup> confi<sub>gura</sub>ti<sub>on</sub> $( x _ { 1 } ^ { * } , . . x _ { k } ^ { * } )$ is likel<sub>y</sub> to contain the zeros of <sub>w</sub> in $I ,$ we can retrieve several roots (accordin<sub>g</sub> to k) and o<sub>p</sub>timizin<sub>g</sub> <sub>p</sub>rocedures d<sub>o</sub> <sub>no</sub>t <sub>requ</sub>i<sub>re</sub> <sub>s</sub>i<sub>gn</sub> <sub>c</sub>h<sub>ange</sub> b<sub>e</sub>t<sub>ween</sub> th<sub>e</sub> b<sub>oun</sub>d<sub>s.</sub>

We <sub>p</sub>erform this o<sub>p</sub>timization in both intervals so we <sub>g</sub>et a list of candidates to maximize the likelihood (the case $x = 0$ is also treated). W<sub>e</sub> k<sub>eep</sub> th<sub>e</sub> b<sub>es</sub>t <sub>o</sub>f th<sub>em an</sub>d <sub>we re</sub>t<sub>r</sub>i<sub>eve</sub> th<sub>e</sub> b<sub>es</sub>t <sub>parame</sub>t<sub>ers</sub> f<sub>or</sub> th<sub>e</sub> GPD fit<sub>.</sub>

4.3.3 Initial threshold. We have detailed the Grimshaw procedure (3.4.2 and 4.3) and how the final threshold $z _ { q }$ i<sub>s ca</sub>l<sub>cu</sub>l<sub>a</sub>t<sub>e</sub>d (e<sub>q</sub>uation 1) but we have not dealt with the initial threshold t. In <sub>prac</sub>ti<sub>ce,</sub> it<sub>s</sub> <sub>va</sub>l<sub>ue</sub> i<sub>s</sub> <sub>no</sub>t <sub>paramoun</sub>t <sub>excep</sub>t th<sub>a</sub>t it <sub>mus</sub>t b<sub>e</sub> “hi<sub>g</sub>h" enou<sub>g</sub>h. The hi<sub>g</sub>her is $t ,$ the more relevant will be the GPD fit (low bias). However, if t is too hi<sub>g</sub>h, the <sub>p</sub>eaks set $\mathbf { Y } _ { t }$ <sub>wou</sub>ld b<sub>e</sub> littl<sub>e</sub> fill<sub>e</sub>d in, so the model would be more variable (hi<sub>g</sub>h variance). The onl<sub>y</sub> <sup>i</sup>mpor<sup>t</sup>an<sup>t</sup> con<sup>diti</sup>on <sup>i</sup>s <sup>t</sup>o ensure <sup>th</sup>a<sup>t</sup> t <sup>i</sup>s <sup>l</sup>ower <sup>th</sup>an $z _ { q } ,$ mean<sup>i</sup>n<sub>g</sub> <sup>th</sup>a<sup>t th</sup>e pro<sup>b</sup>a<sup>bilit</sup>y assoc<sup>i</sup>a<sup>t</sup>e<sup>d t</sup>o t mus<sup>t b</sup>e <sup>l</sup>ower <sup>th</sup>an $1 - q .$ In <sub>p</sub>ractice we set t to a hi<sub>g</sub>h em<sub>p</sub>irical <sub>q</sub>uantile (98%).

A method based on the mean excess plot [10] could be used to set t <sup>i</sup>n a smar<sup>t</sup>er way <sup>b</sup>u<sup>t</sup> <sup>it</sup> <sup>i</sup>s <sup>l</sup>ess s<sup>t</sup>a<sup>bl</sup>e an<sup>d</sup> <sup>lik</sup>e<sup>l</sup>y <sup>t</sup>o ou<sup>t</sup>pu<sup>t</sup> a<sup>b</sup>sur<sup>d</sup> <sub>va</sub>l<sub>ues.</sub>

## 5 EXPERIMENTS

In thi<sub>s</sub> <sub>sec</sub>ti<sub>o</sub>n <sub>we</sub> <sub>app</sub>l<sub>y</sub> b<sub>o</sub>th <sub>ou</sub>r <sub>a</sub>l<sub>go</sub>rithm<sub>s</sub> SPOT <sub>a</sub>nd DSPOT <sub>o</sub>n <sub>severa</sub>l <sub>con</sub>t<sub>ex</sub>t<sub>s.</sub> Fi<sub>rs</sub>t<sub>,</sub> <sub>we</sub> <sub>compare</sub> th<sub>e</sub> <sub>compu</sub>t<sub>e</sub>d th<sub>res</sub>h<sub>o</sub>ld $z _ { q }$ <sub>w</sub>ith th<sub>e</sub> th<sub>eore</sub>ti<sub>ca</sub>l <sub>ones</sub> th<sub>roug</sub>h <sub>exper</sub>i<sub>men</sub>t<sub>s</sub> <sub>on</sub> <sub>syn</sub>th<sub>e</sub>ti<sub>c</sub> d<sub>a</sub>t<sub>a.</sub> Th<sub>en</sub> we use real world datasets from several fields (network, <sub>p</sub>h<sub>y</sub>sics, finance) to hi<sub>g</sub>hli<sub>g</sub>ht the <sub>p</sub>ro<sub>p</sub>erties of our al<sub>g</sub>orithms.

Finall<sub>y</sub> we <sub>p</sub>resent the <sub>p</sub>erformance of our im<sub>p</sub>lementation.

Th<sub>e rea</sub>l <sub>wor</sub>ld d<sub>a</sub>t<sub>ase</sub>t<sub>s use</sub>d i<sub>n</sub> th<sub>ese exper</sub>i<sub>men</sub>t<sub>s are a</sub>ll <sub>ava</sub>il<sub>-</sub> <sub>a</sub>bl<sub>e on</sub> th<sub>e</sub> I<sub>n</sub>t<sub>erne</sub>t <sub>an</sub>d <sub>we</sub> d<sub>o our u</sub>t<sub>mos</sub>t t<sub>o</sub> d<sub>e</sub>t<sub>a</sub>il <sub>exper</sub>i<sub>men</sub>t<sub>a</sub>l <sub>p</sub>rotocols makin<sub>g</sub> them totall<sub>y</sub> re<sub>p</sub>roducible. Our python3 im<sub>p</sub>lementation is available at [1].

## 5.1 (D)SPOT reliability

I<sub>n</sub> thi<sub>s sec</sub>ti<sub>on, we compare our compu</sub>t<sub>e</sub>d th<sub>res</sub>h<sub>o</sub>ld $z _ { q }$ t<sub>o</sub> th<sub>e</sub> th<sub>eo-</sub> <sub>re</sub>ti<sub>ca</sub>l <sub>one.</sub> I<sub>n o</sub>th<sub>er wor</sub>d<sub>s, we wan</sub>t t<sub>o c</sub>h<sub>ec</sub>k ${ \mathrm { i f } } \ z _ { q }$ i<sub>s</sub> th<sub>e</sub> d<sub>es</sub>i<sub>re</sub>d threshold (which verifies $\mathbb { P } ( X > z _ { q } ) < q )$ <sub>.</sub> In th<sub>e sa</sub>m<sub>e</sub> tim<sub>e we</sub> <sub>eva</sub>l<sub>ua</sub>t<sub>e</sub> th<sub>e</sub> i<sub>mpac</sub>t <sub>o</sub>f th<sub>e</sub> <sub>num</sub>b<sub>er</sub> <sub>o</sub>f <sub>o</sub>b<sub>serva</sub>ti<sub>ons</sub> <sub>n</sub> i<sub>n</sub> th<sub>e</sub> i<sub>n</sub>iti<sub>a</sub>l b<sub>a</sub>t<sub>c</sub>h<sub>.</sub>

In the followin<sub>g</sub> ex<sub>p</sub>eriments we set $q = 1 0 ^ { - 3 }$ <sub>a</sub>nd <sub>we</sub> r<sub>u</sub>n SPOT on Ga<sub>u</sub>ssian <sub>w</sub>hite noises of 15000 <sub>v</sub>al<sub>u</sub>es<sub>,</sub> i.e. 15000 inde<sub>p</sub>endent <sub>va</sub>l<sub>ues</sub> f<sub>rom a s</sub>t<sub>an</sub>d<sub>ar</sub>d <sub>norma</sub>l di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on</sub> $( \mu = 0 , \sigma ^ { 2 } = 1 ) .$ F<sub>o</sub>r diferent values of <sub>n</sub> (300, 500, 1000, 2000 and 5000), we run SPOT $k = 1 0 0$ times and we retrieve the avera<sub>g</sub>ed error made in com<sub>p</sub>ari <sub>son</sub> t<sub>o</sub> th<sub>e</sub> th<sub>eore</sub>ti<sub>ca</sub>l th<sub>res</sub>h<sub>o</sub>ld<sub>:</sub>

$$
\text { error   rate } = \left| \frac {z ^ {\mathrm{SPOT}} - z ^ {\mathrm{th}}}{z ^ {\mathrm{th}}} \right|.
$$

Here, $z ^ { \mathrm { t h } }$ i<sub>s</sub> th<sub>e quan</sub>til<sub>e o</sub>f th<sub>e s</sub>t<sub>an</sub>d<sub>ar</sub>d <sub>norma</sub>l di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on a</sub>t l<sub>eve</sub>l $1 - q , \mathrm { { s o } } \ z ^ { \mathrm { { t h } } } \simeq 3 . 0 9$ <sub>.</sub> Th<sub>e</sub> fi<sub>gure</sub> 5 <sub>presen</sub>t<sub>s</sub> th<sub>e</sub> <sub>resu</sub>lt<sub>s.</sub>

Fi<sub>rs</sub>t <sub>o</sub>f <sub>a</sub>ll th<sub>e curves s</sub>h<sub>ow</sub> th<sub>a</sub>t<sub>,</sub> f<sub>or a</sub>ll i<sub>n</sub>iti<sub>a</sub>l b<sub>a</sub>t<sub>c</sub>h <sub>s</sub>i<sub>zes n,</sub> th<sub>e</sub> <sub>error</sub> i<sub>s</sub> l<sub>ow</sub> <sub>an</sub>d d<sub>ecreases</sub> <sub>w</sub>h<sub>en</sub> th<sub>e</sub> <sub>num</sub>b<sub>er</sub> <sub>o</sub>f <sub>o</sub>b<sub>serva</sub>ti<sub>ons</sub> i<sub>ncreases.</sub> It <sub>means</sub> th<sub>a</sub>t th<sub>e</sub> <sub>compu</sub>t<sub>e</sub>d th<sub>res</sub>h<sub>o</sub>ld $z ^ { \mathrm { S P O T } }$ i<sub>s</sub> <sub>c</sub>l<sub>ose</sub> t<sub>o</sub> th<sub>e</sub> th<sub>eore</sub>ti<sub>ca</sub>l <sub>one an</sub>d t<sub>en</sub>d<sub>s</sub> t<sub>o</sub> it<sub>.</sub>

S<sub>econ</sub>dl<sub>y,</sub> <sub>we</sub> h<sub>ave</sub> t<sub>o</sub> <sub>no</sub>ti<sub>ce</sub> th<sub>a</sub>t th<sub>e</sub> <sub>error</sub> <sub>curves</sub> <sub>a</sub>ll <sub>converge</sub> t<sub>o</sub> th<sub>e same va</sub>l<sub>ue regar</sub>dl<sub>ess o</sub>f <sub>n.</sub> Th<sub>ere</sub>f<sub>ore, n</sub> i<sub>s no</sub>t <sub>a paramoun</sub>t parameter. In our experiments, we just <sup>h</sup>ave to ensure t<sup>h</sup>at n is not t<sub>oo</sub> <sub>sma</sub>ll<sub>,</sub> <sub>o</sub>th<sub>erw</sub>i<sub>se</sub> th<sub>e</sub> i<sub>n</sub>iti<sub>a</sub>li<sub>za</sub>ti<sub>on</sub> <sub>s</sub>t<sub>ep</sub> i<sub>s</sub> lik<sub>e</sub>l<sub>y</sub> t<sub>o</sub> f<sub>a</sub>il b<sub>ecause</sub> <sub>o</sub>f <sub>a</sub> l<sub>ac</sub>k <sub>o</sub>f <sub>pea</sub>k<sub>s</sub> t<sub>o per</sub>f<sub>orm</sub> th<sub>e</sub> GPD fit<sub>.</sub> G<sub>enera</sub>ll<sub>y, we use</sub> $n \simeq 1 0 0 0$

![](images/9c44976b51a175fc9543c0b012d786a7608fed822fcf155e17d944657d761724.jpg)  
Figure 5: Error rate with the number of observations accord ing to the batch size n

## 5.2 Finding anomalies with SPOT

5.2.1 Intrusion detection example. SPOT com utes a robust thresh-<sub>o</sub>ld <sub>es</sub>ti<sub>ma</sub>ti<sub>on</sub> $( z _ { q } ) \colon$ th<sub>e more</sub> d<sub>a</sub>t<sub>a we mon</sub>it<sub>or,</sub> th<sub>e more accura</sub>t<sub>e</sub> th<sub>e</sub> <sub>es</sub>ti<sub>ma</sub>ti<sub>on</sub> i<sub>s.</sub> S<sub>o</sub> h<sub>av</sub>i<sub>ng</sub> <sub>a</sub> l<sub>o</sub>t <sub>o</sub>f d<sub>a</sub>t<sub>a</sub> f<sub>rom</sub> th<sub>e</sub> <sub>same</sub> <sub>an</sub>d <sub>un</sub> k<sub>nown</sub> di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on,</sub> SPOT <sub>can gra</sub>d<sub>ua</sub>ll<sub>y a</sub>d<sub>ap</sub>t thi<sub>s</sub> th<sub>res</sub>h<sub>o</sub>ld i<sub>n</sub> <sub>or</sub>d<sub>er</sub> t<sub>o</sub> d<sub>e</sub>t<sub>ec</sub>t <sub>anoma</sub>li<sub>es.</sub> C<sub>y</sub>b<sub>er-secur</sub>it<sub>y</sub> i<sub>s</sub> <sub>a</sub> t<sub>yp</sub>i<sub>ca</sub>l fi<sub>e</sub>ld <sub>w</sub>h<sub>ere</sub> such confi<sub>g</sub>urations a<sub>pp</sub>ear.

To test o<sub>u</sub>r al<sub>g</sub>orithm we <sub>u</sub>se real data from the MAWI re<sub>p</sub>ositor<sub>y</sub> which contains dail<sub>y</sub> network ca<sub>p</sub>tures (15 minutes a da<sub>y</sub> stored in a .pcap file). In these ca<sub>p</sub>tures, MAWIlab [19] finds anomalies and labels them with the taxonomy proposed by Mazel et al. [25]. The <sub>anoma</sub>li<sub>es are re</sub>f<sub>erre</sub>d th<sub>roug</sub>h d<sub>e</sub>t<sub>a</sub>il<sub>e</sub>d <sub>pa</sub>tt<sub>erns.</sub> T<sub>o</sub> b<sub>e c</sub>l<sub>ose</sub> t<sub>o rea</sub>l monitorin<sub>g</sub> s<sub>y</sub>stems we converted raw .pcap files into NetFlow f<sub>orma</sub>t<sub>,</sub> <sub>w</sub>hi<sub>c</sub>h <sub>aggrega</sub>t<sub>es</sub> <sub>pac</sub>k<sub>e</sub>t<sub>s</sub> <sub>an</sub>d <sub>re</sub>t<sub>r</sub>i<sub>eves</sub> <sub>me</sub>t<sub>a-</sub>d<sub>a</sub>t<sub>a</sub> <sub>on</sub>l<sub>y,</sub> <sub>an</sub>d i<sub>s common</sub>l<sub>y use</sub>d t<sub>o measure ne</sub>t<sub>wor</sub>k <sub>ac</sub>ti<sub>v</sub>it<sub>y.</sub> Th<sub>en we</sub> l<sub>a</sub>b<sub>e</sub>l<sub>e</sub>d the flows accordin<sub>g</sub> to the <sub>p</sub>atterns <sub>g</sub>iven b<sub>y</sub> the MAWIlab. In this <sub>exper</sub>i<sub>men</sub>t <sub>we</sub> <sub>use</sub> th<sub>e</sub> t<sub>wo</sub> <sub>cap</sub>t<sub>ures</sub> f<sub>rom</sub> th<sub>e</sub> 17/08/2012 <sub>an</sub>d th<sub>e</sub> 18/08/2012.

Classical attacks are network scans where man<sub>y</sub> SYN <sub>p</sub>ackets <sub>are sen</sub>t i<sub>n or</sub>d<sub>er</sub> t<sub>o</sub> fi<sub>n</sub>d <sub>open an</sub>d <sub>po</sub>t<sub>en</sub>ti<sub>a</sub>ll<sub>y vu</sub>l<sub>nera</sub>bl<sub>e por</sub>t<sub>s on</sub> <sub>severa</sub>l <sub>mac</sub>hi<sub>nes.</sub> A <sub>re</sub>l<sub>evan</sub>t f<sub>ea</sub>t<sub>ure</sub> t<sub>o</sub> d<sub>e</sub>t<sub>ec</sub>t <sub>suc</sub>h <sub>a</sub>tt<sub>ac</sub>k i<sub>s</sub> th<sub>e</sub> ratio of SYN <sub>p</sub>ackets in a <sub>g</sub>iven time window [17]. From our NetFlow records we com<sub>p</sub>ute this feature on successive 50 ms time windows <sub>a</sub>nd <sub>we</sub> tr<sub>y</sub> t<sub>o</sub> find <sub>e</sub>xtr<sub>e</sub>m<sub>e eve</sub>nt<sub>s.</sub> T<sub>o</sub> initi<sub>a</sub>liz<sub>e</sub> SPOT <sub>we use</sub> th<sub>e</sub> l<sub>as</sub>t 1000 <sub>va</sub>l<sub>ues o</sub>f th<sub>e</sub> 17/08 <sub>recor</sub>d <sub>an</sub>d <sub>we</sub> l<sub>e</sub>t th<sub>e a</sub>l<sub>gor</sub>ith<sub>m wor</sub>ki<sub>ng</sub> on the 18/08 ca ture.

![](images/af2327d87fe787e75d9e2ea4fe4d3033d95cb7ebaa5ec1306e19c335ac0483ee.jpg)  
Figure 6: SYN flood detection at level $q = 1 0 ^ { - 4 }$

The fi<sub>g</sub>ure 6 shows the alerts tri<sub>gg</sub>ered b<sub>y</sub> SPOT (red circles). We <sub>reca</sub>ll th<sub>a</sub>t <sub>eac</sub>h <sub>po</sub>i<sub>n</sub>t <sub>represen</sub>t<sub>s</sub> <sub>a</sub> 50 <sub>ms</sub> <sub>w</sub>i<sub>n</sub>d<sub>ow</sub> <sub>ga</sub>th<sub>er</sub>i<sub>ng</sub> <sub>severa</sub>l flows (<sub>p</sub>ossibl<sub>y</sub> beni<sub>g</sub>n and malicious). The com<sub>p</sub>uted threshold (dashed line) seems nearl<sub>y</sub> constant but this behavior is due to the stabilit<sub>y</sub> of the measure we monitor (SPOT has <sub>q</sub>uickl<sub>y</sub> inferred the behavior of the feature). B<sub>y</sub> fla<sub>gg</sub>in<sub>g</sub> all the flows in the tri<sub>gg</sub>ered windows<sub>,</sub> we <sub>g</sub>et a true <sub>p</sub>ositive rate e<sub>q</sub>ual to 86% with less than 4% <sub>o</sub>f f<sub>a</sub>l<sub>se pos</sub>iti<sub>ves.</sub>

5.2.2 The parameter q as a false-positive regulator. In the previo<sub>u</sub>s section we noticed that the size of the initial batch <sub>n</sub> is not <sub>an</sub> i<sub>mpor</sub>t<sub>an</sub>t <sub>parame</sub>t<sub>er</sub> i<sub>nso</sub>f<sub>ar as</sub> it d<sub>oes no</sub>t <sub>a</sub>f<sub>ec</sub>t th<sub>e overa</sub>ll beha<sub>v</sub>ior of SPOT. Here<sub>, w</sub>e st<sub>u</sub>d<sub>y</sub> the im<sub>p</sub>act of the main <sub>p</sub>arameter <sub>q o</sub>n th<sub>e</sub> MAWI d<sub>a</sub>t<sub>ase</sub>t<sub>.</sub>

O<sub>n</sub> th<sub>e</sub> fi<sub>gure</sub> 7<sub>,</sub> th<sub>e</sub> ROC <sub>curve s</sub>h<sub>ows</sub> th<sub>e e</sub>f<sub>ec</sub>t <sub>o</sub>f<sub>q on</sub> th<sub>e</sub> F<sub>a</sub>l<sub>se</sub> Positive rate (FPr). Values of <sub>q</sub> between $1 0 ^ { - 3 }$ <sub>an</sub>d $1 0 ^ { - 5 }$ <sub>a</sub>ll<sub>ow</sub> t<sub>o</sub> h<sub>ave</sub> a hi<sub>g</sub>h TPr while kee<sub>p</sub>in<sub>g</sub> a low FPr: this leaves some room for error w<sup>h</sup>en sett<sup>i</sup>n<sub>g q</sub>.

## 5.3 Finding anomalies with DSPOT

5.3.1 Measure ofthe magneticfield. To show the wide variety <sub>o</sub>f fi<sub>e</sub>ld<sub>s on w</sub>hi<sub>c</sub>h <sub>we can use</sub> DSPOT<sub>, we a</sub> l <sub>our a</sub>l <sub>or</sub>ith<sub>m on</sub> astro<sub>p</sub>h<sub>y</sub>sics measures from the SPIDR (S<sub>p</sub>ace Ph<sub>y</sub>sics Interactive Data Resource) [4]. SPIDR is an online <sub>p</sub>latform which stores and mana<sub>g</sub>es historical s<sub>p</sub>ace <sub>p</sub>h<sub>y</sub>sics data for inte<sub>g</sub>ration with environ <sub>men</sub>t <sub>mo</sub>d<sub>e</sub>l<sub>s</sub> <sub>an</sub>d <sub>space</sub> <sub>wea</sub>th<sub>er</sub> f<sub>orecas</sub>t<sub>s.</sub>

![](images/b948b52dfc2ffee6e957311ee6902a71b630275ac24744155546cac8cb8bec2e.jpg)  
Figure 7: ROC curves on MAWI dataset (the markers give the corresponding value of q)

Partic<sub>u</sub>larl<sub>y</sub> <sub>w</sub>e <sub>u</sub>se a dataset a<sub>v</sub>ailable on Com<sub>p</sub>-En<sub>g</sub>ine Time Series [3] which <sub>g</sub>athers some <sub>p</sub>h<sub>y</sub>sical measures taken b<sub>y</sub> the ACE satellite between 1/1/1995 and 1/6/1995. In the fi<sub>g</sub>ure 8 we monitor a com<sub>p</sub>onent of the ma<sub>g</sub>netic field (in nT) durin<sub>g</sub> several minutes.

This time series is <sub>v</sub>er<sub>y</sub> nois<sub>y</sub> and contains diferent com<sub>p</sub>lex b<sub>e</sub>h<sub>av</sub>i<sub>o</sub>r<sub>s.</sub> W<sub>e ca</sub>libr<sub>a</sub>t<sub>e</sub> DSPOT <sub>w</sub>ith th<sub>e</sub> $n = 2 0 0 0$ fi<sub>rs</sub>t <sub>va</sub>l<sub>ues an</sub>d <sub>we run on</sub> th<sub>e</sub> 15801 <sub>o</sub>th<sub>ers w</sub>ith $q = 1 0 ^ { - 3 }$ <sub>an</sub>d $d = 4 5 0$ <sub>.</sub> Th<sub>e resu</sub>lt<sub>s</sub> <sub>are</sub> d<sub>ep</sub>i<sub>c</sub>t<sub>e</sub>d <sub>on</sub> th<sub>e</sub> fi<sub>gure</sub> 8<sub>.</sub>

![](images/7f611b078cfa8c38e3099fc1d70e3697292589ac6270b376eba171c4899e443f.jpg)  
Figure 8: DSPOT run with $q = 1 0 ^ { - 3 } , d = 4 5 0$

At th<sub>e</sub> fi<sub>rs</sub>t <sub>g</sub>l<sub>ance,</sub> th<sub>e</sub> b<sub>oun</sub>d<sub>s are</sub> f<sub>o</sub>ll<sub>ow</sub>i<sub>ng</sub> th<sub>e s</sub>i<sub>gna</sub>l <sub>an</sub>d <sub>some</sub> alarms are tri<sub>gg</sub>ered b<sub>y</sub> hi<sub>g</sub>h <sub>p</sub>eaks. After 9000 minutes<sub>,</sub> the u<sub>pp</sub>er b<sub>oun</sub>d <sub>seems</sub> hi<sub>g</sub>h<sub>er</sub> th<sub>an</sub> <sub>expec</sub>t<sub>e</sub>d<sub>.</sub>

T<sub>o</sub> <sub>un</sub>d<sub>ers</sub>t<sub>an</sub>d <sub>w</sub>h<sub>y,</sub> l<sub>e</sub>t <sub>us</sub> di<sub>v</sub>id<sub>e</sub> th<sub>e</sub> <sub>s</sub>i<sub>gna</sub>l i<sub>n</sub>t<sub>o</sub> t<sub>wo</sub> <sub>par</sub>t<sub>s:</sub> b<sub>e</sub>f<sub>ore</sub> <sub>an</sub>d <sub>a</sub>ft<sub>er</sub> 8000 <sub>m</sub>i<sub>nu</sub>t<sub>es.</sub> B<sub>e</sub>f<sub>ore</sub> 8000<sub>,</sub> <sub>we</sub> <sub>can</sub> <sub>o</sub>b<sub>serve</sub> th<sub>a</sub>t “<sub>pea</sub>k<sub>s</sub>" l<sub>ean upwar</sub>d<sub>s</sub> th<sub>e</sub> t<sub>ren</sub>d <sub>a</sub>lth<sub>oug</sub>h th<sub>e oppos</sub>it<sub>e p</sub>h<sub>enomenon appears</sub> <sub>a</sub>ft<sub>e</sub>r 8000<sub>.</sub> D<sub>u</sub>rin<sub>g</sub> th<sub>ese</sub> 8000 fir<sub>s</sub>t min<sub>u</sub>t<sub>es,</sub> DSPOT l<sub>ea</sub>rn<sub>s</sub> th<sub>a</sub>t <sub>pea</sub>k<sub>s</sub> <sub>may</sub> l<sub>ean</sub> <sub>upwar</sub>d<sub>s</sub> th<sub>e</sub> t<sub>ren</sub>d <sub>an</sub>d it k<sub>eeps</sub> thi<sub>s</sub> i<sub>n</sub>f<sub>orma</sub>ti<sub>on</sub> i<sub>n</sub> memor<sub>y</sub>. Hence after 8000 minutes<sub>,</sub> the u<sub>pp</sub>er bound sta<sub>y</sub>s hi<sub>g</sub>h in <sub>or</sub>d<sub>er</sub> t<sub>o accommo</sub>d<sub>a</sub>t<sub>e</sub> f<sub>or poss</sub>ibl<sub>e pea</sub>k<sub>s a</sub>b<sub>ove</sub> th<sub>e</sub> t<sub>ren</sub>d<sub>.</sub> DSPOT h<sub>as</sub> thi<sub>s</sub> b<sub>e</sub>h<sub>av</sub>i<sub>or</sub> b<sub>ecause</sub> it k<sub>eeps a g</sub>l<sub>o</sub>b<sub>a</sub>l <sub>memory o</sub>f <sub>a</sub>ll <sub>pea</sub>k<sub>s</sub> <sub>encoun</sub>t<sub>ere</sub>d<sub>.</sub> If it <sub>was no</sub>t d<sub>es</sub>i<sub>re</sub>d<sub>, un easy mo</sub>difi<sub>ca</sub>ti<sub>on</sub> i<sub>s</sub> t<sub>o</sub> k<sub>eep</sub> only the last k peaks, for a fixed k.

5.3.2 Stock prices. On Thursday the 9th of February 2017, an ex-<sub>p</sub>l<sub>os</sub>i<sub>on</sub> h<sub>appene</sub>d <sub>a</sub>t Fl<sub>amanv</sub>ill<sub>e nuc</sub>l<sub>ear p</sub>l<sub>an</sub>t<sub>,</sub> i<sub>n nor</sub>th<sub>ern</sub> F<sub>rance.</sub> This <sub>p</sub>ower <sub>p</sub>lant is mana<sub>g</sub>ed b<sub>y</sub> EDF<sub>,</sub> a French electricit<sub>y p</sub>rovider. Th<sub>e</sub> i<sub>nc</sub>id<sub>en</sub>t <sub>was no</sub>t i<sub>n</sub> th<sub>e nuc</sub>l<sub>ear zone an</sub>d did <sub>no</sub>t h<sub>ur</sub>t <sub>peop</sub>l<sub>e</sub> [5]. This incident was oficiall<sub>y</sub> declared at 11:00 a.m. makin<sub>g</sub> the EDF stock <sub>p</sub>rice fall down. This recent event encoura<sub>g</sub>ed us to test DSPOT <sub>o</sub>n EDF <sub>s</sub>t<sub>oc</sub>k <sub>p</sub>ri<sub>ces.</sub>

Obviousl<sub>y,</sub> retrievin<sub>g</sub> financial data with hi<sub>g</sub>h resolution is not within ours <sub>g</sub>ras<sub>p</sub>. However, some websites like Goo<sub>g</sub>le Finance [2] <sub>p</sub>ro<sub>p</sub>ose intrada<sub>y</sub> financial data with a record <sub>p</sub>er minute. Goo<sub>g</sub>le Finance kee<sub>p</sub>s these records durin<sub>g</sub> 15 da<sub>y</sub>s<sub>,</sub> so we retrieve the <sub>recor</sub>d<sub>s</sub> f<sub>rom</sub> th<sub>e</sub> 6th t<sub>o</sub> th<sub>e</sub> 8th <sub>o</sub>f F<sub>e</sub>b<sub>ruary</sub> 2017 f<sub>or</sub> <sub>ca</sub>lib<sub>ra</sub>ti<sub>on</sub> (1062 values) and ran DSPOT on the ex<sub>p</sub>losion da<sub>y</sub> (379 values). .

On fi<sub>g</sub>ure 9<sub>,</sub> we notice that DSPOT follows the avera<sub>g</sub>e behavior <sub>an</sub>d fl<sub>ags</sub> th<sub>e</sub> d<sub>rop</sub> <sub>aroun</sub>d 11<sub>:</sub>00 <sub>a.m.</sub> Thi<sub>s</sub> <sub>may</sub> h<sub>e</sub>l<sub>p</sub> <sub>a</sub> t<sub>ra</sub>di<sub>ng</sub> <sub>sys</sub>t<sub>em</sub> to <sub>q</sub>uickl<sub>y</sub> take actions or warn ex<sub>p</sub>erts.

![](images/8e8419e5cc584a9d3fe4c0b214c04deb39250cdf89dfb8793b15c9590533cffe.jpg)  
Figure 9: DSPOT run with $q = 1 0 ^ { - 3 }$ $d = 1 0$

## 5.4 Performances

Here we <sub>g</sub>ive some details about the time and memor<sub>y</sub> <sub>p</sub>erformances of our python3 im<sub>p</sub>lementation. All these ex<sub>p</sub>eriments have been made on a la<sub>p</sub>to<sub>p</sub> with an Intel i5-5300U CPU @ 2.30GHz (4 cores) <sub>a</sub>nd 8 GB RAM<sub>.</sub>

B<sub>o</sub>th <sub>a</sub>l<sub>go</sub>rithm<sub>s,</sub> SPOT <sub>a</sub>nd DSPOT r<sub>equ</sub>ir<sub>e a</sub> fix<sub>e</sub>d m<sub>e</sub>m<sub>o</sub>r<sub>y s</sub>iz<sub>e</sub> f<sub>or</sub> <sub>a</sub>ll th<sub>e</sub> <sub>var</sub>i<sub>a</sub>bl<sub>es</sub> <sub>excep</sub>t f<sub>or</sub> th<sub>e</sub> <sub>pea</sub>k <sub>se</sub>t $\mathbf { Y } _ { t }$ which ma<sub>y</sub> <sub>g</sub>row with th<sub>e</sub> <sub>num</sub>b<sub>er</sub> <sub>o</sub>f <sub>o</sub>b<sub>serva</sub>ti<sub>ons.</sub> T<sub>o</sub> <sub>measure</sub> th<sub>e</sub> <sub>memory</sub> <sub>per</sub>f<sub>ormance</sub> <sub>o</sub>f <sub>our</sub> <sub>a</sub>l<sub>gor</sub>ith<sub>m</sub> <sub>we</sub> <sub>repor</sub>t th<sub>e</sub> <sub>num</sub>b<sub>er</sub> <sub>o</sub>f <sub>pea</sub>k<sub>s</sub> <sub>we</sub> <sub>s</sub>t<sub>ore</sub>d<sub>.</sub>

T<sub>o</sub> t<sub>es</sub>t th<sub>e per</sub>f<sub>ormances o</sub>f <sub>our a</sub>l<sub>gor</sub>ith<sub>ms we run eac</sub>h <sub>o</sub>f th<sub>em</sub> on 100 Gaussian white noises of15000 values (like the ex<sub>p</sub>eriment in section 5.1). At ever<sub>y</sub> run we measure the avera<sub>g</sub>ed time to <sub>p</sub>erform <sub>one</sub> it<sub>era</sub>ti<sub>on</sub> <sub>an</sub>d th<sub>e</sub> <sub>ra</sub>ti<sub>o</sub> <sub>o</sub>f <sub>s</sub>t<sub>ore</sub>d <sub>pea</sub>k<sub>s,</sub> i<sub>.e.</sub> th<sub>e</sub> <sub>num</sub>b<sub>er</sub> <sub>o</sub>f <sub>pea</sub>k<sub>s</sub> <sub>over</sub> th<sub>e num</sub>b<sub>er o</sub>f <sub>o</sub>b<sub>serva</sub>ti<sub>ons.</sub>

F<sub>o</sub>r th<sub>ese e</sub>x<sub>pe</sub>rim<sub>e</sub>nt<sub>s we se</sub>t $q = 1 0 \AA ^ { - 3 }$ and we use n = 1000 <sub>va</sub>l<sub>ues</sub> f<sub>or</sub> th<sub>e</sub> i<sub>n</sub>iti<sub>a</sub>l b<sub>a</sub>t<sub>c</sub>h<sub>.</sub> W<sub>e recor</sub>d th<sub>ese measures</sub> i<sub>n</sub> f<sub>our con-</sub> texts: SPOT, SPOT both sides (bi-SPOT), DSPOT and DSPOT both sides (bi-DSPOT). The “both sides" runs take into account u<sub>pp</sub>er <sub>an</sub>d l<sub>ower</sub> th<sub>res</sub>h<sub>o</sub>ld<sub>s up</sub>d<sub>a</sub>t<sub>es.</sub> I<sub>n</sub> d<sub>r</sub>ifti<sub>ng cases, we a</sub>dd <sub>a</sub> d<sub>r</sub>ift t<sub>o</sub> the Gaussian white noise and we use a depth d = 50.

The table 2 <sub>p</sub>resents the avera<sub>g</sub>ed time to <sub>p</sub>erform one iteration (denoted T, measured in <sub>µ</sub>s) and the ratio number of <sub>p</sub>eaks over number of observations at the end of the run (denoted M, in %) in <sub>mean,</sub> b<sub>es</sub>t <sub>an</sub>d <sub>wors</sub>t <sub>cases.</sub>

<table><tr><td rowspan="2">Method</td><td colspan="2">Worst</td><td colspan="2">Mean</td><td colspan="2">Best</td></tr><tr><td>T</td><td>M</td><td>T</td><td>M</td><td>T</td><td>M</td></tr><tr><td>SPOT</td><td>959</td><td>2,70</td><td>351</td><td>1,90</td><td>141</td><td>1,40</td></tr><tr><td>DSPOT</td><td>883</td><td>3,49</td><td>391</td><td>2,02</td><td>197</td><td>1,07</td></tr><tr><td>bi-SPOT</td><td>1733</td><td>5,58</td><td>772</td><td>4,18</td><td>373</td><td>2,79</td></tr><tr><td>bi-DSPOT</td><td>1053</td><td>5,79</td><td>591</td><td>4,02</td><td>272</td><td>2,74</td></tr></table>

Table 2: Time (T, in µs) and Memory (M, in %) performances

Our al<sub>g</sub>orithm stores a little ratio of all the stream (few <sub>p</sub>ercents). Lo<sub>g</sub>icall<sub>y</sub> we store about twice more when we com<sub>p</sub>ute u<sub>pp</sub>er and l<sub>ower</sub> th<sub>res</sub>h<sub>o</sub>ld<sub>s.</sub> E<sub>ven</sub> if th<sub>e</sub> <sub>grow</sub>th <sub>spee</sub>d <sub>o</sub>f th<sub>e</sub> <sub>pea</sub>k<sub>s</sub> <sub>se</sub>t<sub>s</sub> <sub>s</sub>i<sub>ze</sub> i<sub>s</sub> l<sub>ow</sub> it <sub>cou</sub>ld b<sub>e</sub> <sub>an</sub> hi<sub>n</sub>d<sub>rance</sub> f<sub>or</sub> <sub>a</sub> l<sub>ong</sub> t<sub>erm</sub> <sub>mon</sub>it<sub>or</sub>i<sub>ng.</sub> H<sub>owever,</sub> the size ofthe <sub>p</sub>eaks set could be u<sub>pp</sub>er-bounded (with a hi<sub>g</sub>h bound) makin<sub>g</sub> it work like a wide slidin<sub>g</sub> window (ver<sub>y</sub> old <sub>p</sub>eaks would be dro<sub>pp</sub>ed) without loss of accurac<sub>y</sub>.

Fi<sub>na</sub>ll<sub>y</sub> th<sub>e</sub> ti<sub>me per</sub>f<sub>ormances o</sub>f <sub>our a</sub>l<sub>gor</sub>ith<sub>ms s</sub>h<sub>ow</sub> th<sub>a</sub>t <sub>our</sub> i<sub>mp</sub>l<sub>emen</sub>t<sub>a</sub>ti<sub>on</sub> i<sub>s a</sub>bl<sub>e</sub> t<sub>o wor</sub>k <sub>on s</sub>t<sub>reams w</sub>ith <sub>more</sub> th<sub>an</sub> 1000 <sub>va</sub>l<sub>ues a secon</sub>d<sub>.</sub>

## 6 CONCLUSION

This <sub>p</sub>a<sub>p</sub>er has <sub>p</sub>resented a novel a<sub>pp</sub>roach to detect outliers in hi<sub>g</sub>h throu<sub>g</sub>h<sub>p</sub>ut numerical time series. The ke<sub>y</sub> <sub>p</sub>oints of our a<sub>pp</sub>roach i<sub>s</sub> th<sub>a</sub>t it d<sub>oes no</sub>t <sub>assume</sub> th<sub>e</sub> d<sub>a</sub>t<sub>a</sub> di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on, an</sub>d it d<sub>oes no</sub>t <sub>requ</sub>i<sub>re manua</sub>ll<sub>y se</sub>t th<sub>res</sub>h<sub>o</sub>ld<sub>s.</sub> It <sub>a</sub>d<sub>ap</sub>t<sub>s on mu</sub>lti<sub>p</sub>l<sub>e an</sub>d <sub>comp</sub>l<sub>ex</sub> <sub>con</sub>t<sub>ex</sub>t<sub>s,</sub> l<sub>earn</sub>i<sub>ng</sub> h<sub>ow</sub> th<sub>e</sub> i<sub>n</sub>t<sub>eres</sub>t <sub>measure</sub> b<sub>e</sub>h<sub>aves.</sub> It <sub>ac</sub>hi<sub>eves</sub> these results b<sub>y</sub> usin<sub>g</sub> the Extreme Values Theor<sub>y</sub> (EVT). To the b<sub>es</sub>t <sub>o</sub>f <sub>our</sub> k<sub>now</sub>l<sub>e</sub>d<sub>ge,</sub> it i<sub>s</sub> th<sub>e</sub> fi<sub>rs</sub>t ti<sub>me</sub> EVT h<sub>as</sub> b<sub>een use</sub>d t<sub>o</sub> detect outliers in streamin<sub>g</sub> data.

Th<sub>ere are</sub> t<sub>wo</sub> ki<sub>n</sub>d<sub>s o</sub>f <sub>perspec</sub>ti<sub>ves.</sub> F<sub>rom</sub> th<sub>e</sub> th<sub>eore</sub>ti<sub>ca</sub>l <sub>s</sub>id<sub>e,</sub> in this <sub>p</sub>a<sub>p</sub>er we onl<sub>y</sub> ex<sub>p</sub>loited a small <sub>p</sub>art of EVT<sub>,</sub> we wo<sub>u</sub>ld lik<sub>e</sub> t<sub>o ex</sub>t<sub>en</sub>d thi<sub>s wor</sub>k t<sub>o</sub> th<sub>e mu</sub>lti<sub>var</sub>i<sub>a</sub>t<sub>e case an</sub>d t<sub>o non-</sub>iid <sub>o</sub>b<sub>serva</sub>ti<sub>ons.</sub>

From the <sub>p</sub>ractical side<sub>,</sub> one of the immediate a<sub>pp</sub>lication of our approach is automatic thresholding: it can provide thresholds with <sub>s</sub>t<sub>rong s</sub>t<sub>a</sub>ti<sub>s</sub>ti<sub>ca</sub>l <sub>guaran</sub>t<sub>ees</sub> th<sub>a</sub>t <sub>can a</sub>d<sub>ap</sub>t t<sub>o</sub> th<sub>e evo</sub>l<sub>u</sub>ti<sub>on o</sub>f <sub>a</sub> d<sub>a</sub>t<sub>a s</sub>t<sub>ream.</sub> W<sub>e wou</sub>ld lik<sub>e</sub> t<sub>o exp</sub>l<sub>ore</sub> th<sub>e use o</sub>f <sub>our approac</sub>h <sub>as a</sub> b<sub>u</sub>ildi<sub>ng</sub> bl<sub>oc</sub>k i<sub>n</sub>t<sub>o more comp</sub>l<sub>ex sys</sub>t<sub>ems</sub> th<sub>a</sub>t <sub>requ</sub>i<sub>re</sub> th<sub>res</sub>h<sub>o</sub>ldi<sub>ng.</sub> Al<sub>so</sub> th<sub>e</sub> EVT <sub>on mu</sub>lti<sub>var</sub>i<sub>a</sub>t<sub>e cases cou</sub>ld <sub>a</sub>dd<sub>ress our pro</sub>bl<sub>em</sub> i<sub>n</sub> more <sub>g</sub>eneral contexts without inde<sub>p</sub>endence condition.

## REFERENCES

[1] htt<sub>p</sub>s://<sub>g</sub>ithub.com/Amoss<sub>y</sub>s-team/SPOT. (????).

[2] Goo<sub>g</sub>le Finance. htt<sub>p</sub>s://www.<sub>g</sub>oo<sub>g</sub>le.com/finance. (????).

[3] Ma<sub>g</sub>netic field time series. htt<sub>p</sub>://www.com<sub>p</sub>-en<sub>g</sub>ine.or<sub>g</sub>/timeseries/time-series\_ data/data-17481/. (????).

[4] S<sub>p</sub>ace Ph<sub>y</sub>sics Interactive Data Resource. htt<sub>p</sub>://s<sub>p</sub>idr.ionosonde.net/s<sub>p</sub>idr/home. do. (????).

[5] htt<sub>p</sub>://www.webcitation.or<sub>g</sub>/6oAx<sub>q</sub>oFkf. (????).

[6] Dee<sub>p</sub>ak A<sub>g</sub>arwal. 2005. An em<sub>p</sub>irical ba<sub>y</sub>es a<sub>pp</sub>roach to detect anomalies in dynamic multidimensional arrays. In ICDM.

[7] Fabrizio An<sub>g</sub>iulli, Stefano Basta, and Clara Pizzuti. 2006. Distance-based detection and prediction of outliers. IEEE transactions on knowledge and data engineering (2006).

[8] Fabrizio An<sub>g</sub>iulli and Fabio Fassetti. 2007. Detectin<sub>g</sub> distance-based outliers in streams of data. In Proceedings ofthe 16th ACM conference on Conference on information and knowledge management.

[9] Au<sub>g</sub>ust A Balkema and Laurens De Haan. 1974. Residual life time at <sub>g</sub>reat a<sub>g</sub>e. The Annals ofprobability (1974).

[10] Jan Beirlant, Yuri Goegebeur, Johan Segers, and Jozef Teugels. 2006. Statistics of extremes: theory and applications. John Wiley & Sons.

[11] Markus M Breuni<sub>g</sub>, Hans-Peter Krie<sub>g</sub>el, Ra<sub>y</sub>mond T N<sub>g</sub>, and Jör<sub>g</sub> Sander. 2000. LOF: identifying density-based local outliers. In ACM sigmod record, Vol. 29. ACM, 93–104.

[12] Richard H B<sub>y</sub>rd, Peihuan<sub>g</sub> Lu, Jor<sub>g</sub>e Nocedal, and Ci<sub>y</sub>ou Zhu. 1995. A limited memory algorithm for bound constrained optimization. SIAM J. on Scientific Computing (1995).

[13] Varun Chandola, Arindam Banerjee, and Vi<sub>p</sub>in Kumar. 2009. Anomal<sub>y</sub> detection: A survey. ACM computing surveys (2009).

[14] Lian Duan, Lida Xu, Yin<sub>g</sub> Liu, and Jun Lee. 2009. Cluster-based outlier detection. Annals ofOperations Research 168 1 (2009) 151–168.

[15] Manzoor Elahi, Kun Li, Wasif Nisar, Xinjie Lv, and Hon<sub>g</sub>an Wan<sub>g</sub>. 2008. Eficient clustering-based outlier detection algorithm for dynamic data stream. In FSKD’08.

[16] Eleazar Eskin. 2000. Anomal<sub>y</sub> detection over nois<sub>y</sub> data usin<sub>g</sub> learned <sub>p</sub>robabilit<sub>y</sub> distributions. In ICML.

[17] Guilherme Fernandes and Phili<sub>pp</sub>e Owezarski. 2009. Automated classification of network trafic anomalies. In ICSPCS.

[18] Ronald A<sub>y</sub>lmer Fisher and Leonard Henr<sub>y</sub> Caleb Ti<sub>pp</sub>ett. 1928. Limitin<sub>g</sub> forms <sub>o</sub>f th<sub>e</sub> f<sub>re uenc</sub> di<sub>s</sub>t<sub>r</sub>ib<sub>u</sub>ti<sub>on o</sub>f th<sub>e</sub> l<sub>ar es</sub>t <sub>or sma</sub>ll<sub>es</sub>t <sub>mem</sub>b<sub>er o</sub>f <sub>a sam</sub> l<sub>e.</sub> I<sub>n</sub> Mathematical Proceedings ofthe Cambridge Philosophical Society.

[19] Romain Fontu<sub>g</sub>ne, Pierre Bor<sub>g</sub>nat, Patrice Abr<sub>y</sub>, and Kensuke Fukuda. 2010. MAWIL<sub>a</sub>b: C<sub>o</sub>mbinin<sub>g</sub> Di<sub>ve</sub>r<sub>se</sub> An<sub>o</sub>m<sub>a</sub>l<sub>y</sub> D<sub>e</sub>t<sub>ec</sub>t<sub>o</sub>r<sub>s</sub> f<sub>o</sub>r A<sub>u</sub>t<sub>o</sub>m<sub>a</sub>t<sub>e</sub>d An<sub>o</sub>m<sub>a</sub>l<sub>y</sub> Labeling and Performance Benchmarking. In ACM CoNEXT ’10.

[20] Boris Gnedenko. 1943. Sur la distribution limite du terme maximum d’une serie aleatoire. Annals ofmathematics (1943), 423–453

[21] Scott D. Grimshaw. 1993. Com<sub>p</sub>utin<sub>g</sub> Maximum Likelihood Estim<sub>a</sub>t<sub>es</sub> f<sub>o</sub>r th<sub>e</sub> G<sub>e</sub>n<sub>e</sub>r<sub>a</sub>liz<sub>e</sub>d P<sub>a</sub>r<sub>e</sub>t<sub>o</sub> Di<sub>s</sub>trib<sub>u</sub>ti<sub>o</sub>n<sub>.</sub> Technometrics 35, 2 (1993), 185–191. htt<sub>p</sub>s://doi.or<sub>g</sub>/10.1080/00401706.1993.10485040 arXiv:htt<sub>p</sub>://amstat.tandfonline.com/doi/<sub>p</sub>df/10.1080/00401706.1993.10485040

[22] Bruce M Hill. 1975. A sim le eneral a roach to inference about the tail of a distribution. The annals ofstatistics 3, 5 (1975), 1163–1174.

[23] Ludmila I Kuncheva. 2008. Classifier ensembles for detectin<sub>g</sub> conce<sub>p</sub>t chan<sub>g</sub>e in streaming data: Overview and perspectives. In 2nd Workshop SUEMA.

[24] Rikard Laxhammar and Göran Falkman. 2014. Online learnin<sub>g</sub> and se<sub>q</sub>uential anomaly detection in trajectories. IEEE transactions on pattern analysis and machine intelligence 36, 6 (2014), 1158–1173.

[25] Johan Mazel, Romain Fontu<sub>g</sub>ne, and Kensuke Fukuda. 2014. A taxonom<sub>y</sub> of anomalies in backbone network trafic. In IWCMC.

[26] EWT N<sub>g</sub>ai, Yon<sub>g</sub> Hu, YH Won<sub>g</sub>, Yijun Chen, and Xin Sun. 2011. The a<sub>pp</sub>lication of d<sub>a</sub>t<sub>a m</sub>i<sub>n</sub>i<sub>ng</sub> t<sub>ec</sub>h<sub>n</sub>i<sub>ques</sub> i<sub>n</sub> fi<sub>nanc</sub>i<sub>a</sub>l f<sub>rau</sub>d d<sub>e</sub>t<sub>ec</sub>ti<sub>on:</sub> A <sub>c</sub>l<sub>ass</sub>ifi<sub>ca</sub>ti<sub>on</sub> f<sub>ramewor</sub>k and an academic review of literature. Decision Support Systems 50, 3 (2011), 559–569.

[27] James Pickands III. 1975. Statistical inference using extreme order statistics. the Annals ofStatistics (1975).

[28] Md Shiblee Sadik and Le Gruenwald. 2010. DBOD-DS: Distance based outlier detection for data streams. In International Conference on Database and Expert Systems Applications. Springer, 122–136.

[29] Shiblee Sadik and Le Gruenwald. 2014. Research issues in outlier detection for data streams. ACM SIGKDD Explorations Newsletter 15, 1 (2014), 33–40.

[30] John E Seem. 2007. Usin<sub>g</sub> intelli<sub>g</sub>ent data anal<sub>y</sub>sis to detect abnormal ener<sub>gy</sub> consum tion in buildin s. Energy and buildings 39, 1 (2007), 52–58.

[31] Dur<sub>g</sub>a Toshniwal. 2012. A framework for outlier detection in evolvin<sub>g</sub> data streams by weighting attributes in clustering. Procedia Technology 6 (2012), 214–222.

[32] Hainin<sub>g</sub> Wan<sub>g</sub>, Danlu Zhan<sub>g</sub>, and Kan<sub>g</sub> G Shin. 2002. Detectin<sub>g</sub> SYN floodin<sub>g</sub> attacks. In INFOCOM.