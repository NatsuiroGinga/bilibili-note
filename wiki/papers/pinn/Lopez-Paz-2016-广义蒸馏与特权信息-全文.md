---
title: "Lopez-Paz-2016-广义蒸馏与特权信息"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "pinn"
source_pdf: "raw/papers/pinn/Lopez-Paz-2016-广义蒸馏与特权信息.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# UNIFYING DISTILLATION AND PRIVILEGED INFORMATION

David Lopez-Paz Facebook AI Research, Paris, France<sup>∗</sup> dlp@fb.com

Leon Bottou´ Facebook AI Research, New York, USA leon@bottou.org

Bernhard Scholkopf¨ Max Planck Insitute for Intelligent Systems, Tubingen, Germany¨ bs@tuebingen.mpg.de

Vladimir Vapnik Facebook AI Research and Columbia University, New York, USA vladimir.vapnik@gmail.com

## ABSTRACT

Distillation (Hinton et al., 2015) and privileged information (Vapnik & Izmailov, 2015) are two techniques that enable machines to learn from other machines. This paper unifies the two into generalized distillation, a framework to learn from multiple machines and data representations. We provide theoretical and causal insight about the inner workings of generalized distillation, extend it to unsupervised, semisupervised and multitask learning scenarios, and illustrate its efficacy on a variety of numerical simulations on both synthetic and real-world data.

## 1 INTRODUCTION

Humans learn much faster than machines. Vapnik & Izmailov (2015) illustrate this discrepancy with the Japanese proverb

better than a thousand days ofdiligent study is one day with a great teacher.

Motivated by this insight, the authors incorporate an “intelligent teacher” into machine learning. Their solution is to consider training data formed by a collection of triplets

$$
\{(x _ {1}, x _ {1} ^ {\star}, y _ {1}), \dots , (x _ {n}, x _ {n} ^ {\star}, y _ {n}) \} \sim P ^ {n} (x, x ^ {\star}, y).
$$

Here, each $( x _ { i } , y _ { i } )$ is a feature-label pair, and the novel element $x _ { i } ^ { \star }$ is additional information about the example $( x _ { i } , y _ { i } )$ provided by an intelligent teacher, such as to support the learning process. Unfortunately, the learning machine will not have access to the teacher explanations $\boldsymbol { x } _ { i } ^ { \star }$ at test time. Thus, the framework of learning using privileged information (Vapnik & Vashist, 2009; Vapnik & Izmailov, 2015) studies how to leverage these explanations $x _ { i } ^ { \star }$ at training time, to build a classifier for test time that outperforms those built on the regular features $x _ { i }$ alone. As an example, $x _ { i }$ could be the image of a biopsy, $\boldsymbol { x } _ { i } ^ { \star }$ the medical report of an oncologist when inspecting the image, and y<sub>i</sub> a binary label indicating whether the tissue shown in the image is cancerous or healthy.

The previous exposition finds a mathematical justification in VC theory (Vapnik, 1998), which characterizes the speed at which machines learn using two ingredients: the capacity or flexibility of the machine, and the amount of data that we use to train it. Consider a binary classifier f belonging to a function class $\mathcal { F }$ with finite VC-Dimension $| \mathcal { F } | _ { \mathrm { V C } }$ . Then, with probability $1 - \delta .$ , the expected error $R ( f )$ is upper bounded by

$$
R (f) \leq R _ {n} (f) + O \left(\left(\frac {| \mathcal {F} | _ {\mathrm{VC}} - \log \delta}{n}\right) ^ {\alpha}\right),\tag{1}
$$

where $R _ { n } ( f )$ is the training error over n data, and $\frac { 1 } { 2 } ~ \leq ~ \alpha ~ \leq ~ 1$ . For difficult (non-separable) problems the exponent is $\alpha = { \textstyle { \frac { 1 } { 2 } } }$ , which translates into machines learning at a slow rate of $O ( n ^ { - 1 / 2 } )$ On the other hand, for easy (separable) problems, i.e., those on which the machine $f$ makes no training errors, the exponent is $\alpha = 1$ , which translates into machines learning at $\textbf { a } f a s t$ rate of $O ( n ^ { - 1 } )$ . The difference between these two rates is huge: the $O ( n ^ { - 1 } )$ learning rate potentially only requires 1000 examples to achieve the accuracy for which the $O ( n ^ { - 1 / 2 } )$ learning rate needs $1 0 ^ { 6 }$ examples. So, given a student who learns from a fixed amount of data n and a function class ${ \mathcal { F } } ,$ , a good teacher can try to ease the problem at hand by accelerating the learning rate from $O ( n ^ { - 1 / 2 } )$ to $\bar { O } ( n ^ { - 1 } )$

Vapnik’s learning using privileged information is one example of what we call machines-teachingmachines: the paradigm where machines learn from other machines, in addition to training data. Another seemingly unrelated example is distillation (Hinton et al., 2015),<sup>1</sup> where a simple machine learns a complex task by imitating the solution of a flexible machine. In a wider context, the machines-teaching-machines paradigm is one step toward the definition of machine reasoning of Bottou (2014), “the algebraic manipulation of previously acquired knowledge to answer a new question”. In fact, many recent state-of-the-art systems compose data and supervision from multiple sources, such as object recognizers reusing convolutional neural network features (Oquab et al., 2014), and natural language processing systems operating on vector word representations extracted from unsupervised text corpora (Mikolov et al., 2013).

In the following, we frame Hinton’s distillation and Vapnik’s privileged information as two instances of the same machines-teaching-machines paradigm, termed generalized distillation. The analysis of generalized distillation sheds light to applications in semi-supervised learning, domain adaptation, transfer learning, Universum learning (Weston et al., 2006), reinforcement learning, and curriculum learning (Bengio et al., 2009); some of them discussed in our numerical simulations.

## 2 DISTILLATION

We focus on c-class classification, although the same ideas apply to regression. Consider the data

$$
\{(x _ {i}, y _ {i}) \} _ {i = 1} ^ {n} \sim P ^ {n} (x, y), x _ {i} \in \mathbb {R} ^ {d}, y _ {i} \in \Delta^ {c}.\tag{2}
$$

Here, $\Delta ^ { c }$ is the set of c-dimensional probability vectors. Using (2), we are interested in learning the representation

$$
f _ {t} = \underset {f \in \mathcal {F} _ {t}} {\arg \min} \frac {1}{n} \sum_ {i = 1} ^ {n} \ell (y _ {i}, \sigma (f (x _ {i}))) + \Omega (\| f \|),\tag{3}
$$

where $\mathcal { F } _ { t }$ is a class of functions from $\mathbb { R } ^ { d }$ to $\mathbb { R } ^ { c }$ , the function $\sigma : \mathbb { R } ^ { c }  \Delta ^ { c }$ is the softmax operation

$$
\sigma (z) _ {k} = \frac {e ^ {z _ {k}}}{\sum_ {j = 1} ^ {c} e ^ {z _ {j}}},
$$

for all $1 \leq k \leq c ,$ , the function $\ell : \Delta ^ { c } \times \Delta ^ { c } \to \mathbb { R } _ { + }$ is the cross-entropy loss

$$
\ell (y, \hat {y}) = - \sum_ {k = 1} ^ {c} y _ {k} \log \hat {y} _ {k},
$$

and $\Omega : \mathbb { R }  \mathbb { R }$ is an increasing function which serves as a regularizer.

When learning from real world data such as high-resolution images, $f _ { t }$ is often an ensemble of large deep convolutional neural networks (LeCun et al., 1998a). The computational cost of predicting new examples at test time using these ensembles is often prohibitive for production systems. For this reason, Hinton et al. (2015) propose to distill the learned representation $f _ { t } \in \mathcal { F } _ { t }$ into

$$
f _ {s} = \underset {f \in \mathcal {F} _ {s}} {\arg \min} \frac {1}{n} \sum_ {i = 1} ^ {n} \left[ (1 - \lambda) \ell (y _ {i}, \sigma (f (x _ {i}))) + \lambda \ell (s _ {i}, \sigma (f (x _ {i}))) \right],\tag{4}
$$

where

$$
s _ {i} = \sigma (f _ {t} (x _ {i}) / T) \in \Delta^ {c}\tag{5}
$$

are the soft predictions from $f _ { t }$ about the training data, and $\mathcal { F } _ { s }$ is a function class simpler than $\mathcal { F } _ { t }$ The temperature parameter $\dot { T } > 0$ controls how much do we want to soften or smooth the classprobability predictions from $f _ { t } ,$ , and the imitation parameter $\lambda \in \ [ 0 , 1 ]$ balances the importance between imitating the soft predictions $s _ { i }$ and predicting the true hard labels $y _ { i }$ . Higher temperatures lead to softer class-probability predictions $s _ { i }$ . In turn, softer class-probability predictions reveal label dependencies which would be otherwise hidden as extremely large or small numbers. After distillation, we can use the simpler $f _ { s } \in \mathcal { F } _ { s }$ for faster prediction at test time.

## 3 VAPNIK’S PRIVILEGED INFORMATION

We now turn back to Vapnik’s problem of learning in the company of an intelligent teacher, as introduced in Section 1. The question at hand is: How can we leverage the privileged information $\boldsymbol { x } _ { i } ^ { \star }$ to build a better classifier for test time? One na¨ıve way to proceed would be to estimate the privileged representation $x _ { i } ^ { \star }$ from the regular representation $x _ { i } ,$ and then use the union of regular and estimated privileged representations as our test-time feature space. But this may be a cumbersome endeavour: in the example of biopsy images $x _ { i }$ and medical reports $\boldsymbol { x } _ { i } ^ { \star }$ , it is reasonable to believe that predicting reports from images is more complicated than classifying the images into cancerous or healthy.

Alternatively, we propose to use distillation to extract useful knowledge from privileged information. The proposal is as follows. First, learn a teacher function $f _ { t } \in \mathcal { F } _ { t }$ by solving $\bar { ( 3 ) }$ using the data $\{ ( x _ { i } ^ { \star } , y _ { i } ) \} _ { i = 1 } ^ { n }$ . Second, compute the teacher soft labels $s _ { i } = \sigma ( f _ { t } ( x _ { i } ^ { \star } ) / T )$ ), for all $1 \leq i \leq n$ and some temperature parameter $T > 0$ . Third, distill $f _ { t } \in \mathcal { F } _ { t }$ into $f _ { s } \in \mathcal { F } _ { s }$ by solving (4) using both the hard labeled data $\{ ( x _ { i } , y _ { i } ) \} _ { i = 1 } ^ { n }$ and the softly labeled data $\{ ( x _ { i } , s _ { i } ) \} _ { i = 1 } ^ { n } .$

## 3.1 COMPARISON TO PRIOR WORK

Vapnik & Vashist (2009); Vapnik & Izmailov (2015) offer two strategies to learn using privileged information: similarity control and knowledge transfer. Let us briefly compare them to our distillationbased proposal.

The motivation behind similarity control is that SVM classification is separable after we correct for the slack values $\xi _ { i }$ , which measure the degree of misclassification of training data points $x _ { i }$ (Vapnik & Vashist, 2009). Since separable classification admits $O ( n ^ { - 1 } )$ fast learning rates, it would be ideal to have a teacher that could supply slack values to us. Unluckily, it seems quixotic to aspire for a teacher able to provide with abstract floating point number slack values. Perhaps it is more realistic to assume instead that the teacher can provide with some rich, high-level representation useful to estimate the sought-after slack values. This reasoning crystallizes into the SVM+ objective function from (Vapnik & Vashist, 2009):

$$
L (w, w ^ {\star}, b, b ^ {\star}, \alpha , \beta) = \underbrace {\frac {1}{2} \| w \| ^ {2} + \sum_ {i = 1} ^ {n} \alpha_ {i} - \sum_ {i = 1} ^ {n} \alpha_ {i} y _ {i} f _ {i}} _ {\text { separable   SVM   objective }} + \underbrace {\frac {\gamma}{2} \| w ^ {\star} \| ^ {2} + \sum_ {i = 1} ^ {n} (\alpha_ {i} + \beta_ {i} - C) f _ {i} ^ {\star}} _ {\text { corrections   from   teacher }},\tag{6}
$$

where $f _ { i } : = \langle w , x _ { i } \rangle + b$ is the decision boundary at $x _ { i }$ , and $f _ { i } ^ { \star } : = \langle w ^ { \star } , x _ { i } ^ { \star } \rangle + b ^ { \star }$ is the teacher correcting function at the same location. The SVM+ objective function matches the objective function of non-separable SVM when we replace the correcting functions $f _ { i } ^ { \star }$ with the slacks $\xi _ { i }$ . Thus, skilled teachers provide with privileged information $x _ { i } ^ { \star }$ highly informative about the slack values $\xi _ { i } .$ . Such privileged information allows for simple correcting functions $f _ { i } ^ { \star }$ , and the easy estimation of these correcting functions is a proxy to $O ( \overset { \cdot } { n } ^ { - 1 } )$ fast learning rates. Technically, this amounts to saying that a teacher is helpful whenever the capacity of her correcting functions is much smaller than the capacity of the student decision boundary.

In knowledge transfer (Vapnik & Izmailov, 2015) the teacher fits a function $\begin{array} { r l } { f _ { t } ( x ^ { \star } ) } & { { } = } \end{array}$ ${ \textstyle \sum _ { j = 1 } ^ { m } \alpha _ { j } ^ { \star } k ^ { \star } \big ( } u _ { j } ^ { \star } , x ^ { \star } )$ on the input-output pairs $\{ ( x _ { i } ^ { \star } , y _ { i } ) \} _ { i = 1 } ^ { n }$ and $f _ { t } \in \mathcal { F } _ { t }$ , to find the best reduced set of prototype or basis points $\{ u _ { j } ^ { \star } \} _ { j = 1 } ^ { m } .$ . Second, the student fits one function $g _ { j }$ per set of input-output pairs $\{ ( x _ { i } , k ^ { \star } ( u _ { j } ^ { \star } , x _ { i } ^ { \star } ) ) \} _ { i = 1 } ^ { n }$ , for all $1 \leq j \leq m$ . Third, the student fits a new vector of coefficients $\alpha \in \mathbb { R } ^ { m }$ to obtain the final student function $\begin{array} { r } { f _ { s } ( x ) = \sum _ { j = 1 } ^ { m } \alpha _ { j } g _ { j } ( x ) } \end{array}$ , using the input-output pairs $\{ ( x _ { i } , y _ { i } ) \} _ { i = 1 } ^ { n }$ and $f _ { s } \in \mathcal { F } _ { s }$ . Since the representation $x _ { i } ^ { \star }$ is intelligent, we assume that the function class $\mathcal { F } _ { t }$ has small capacity, and thus allows for accurate estimation under small sample sizes.

Distillation differs from similarity control in three ways. First, distillation is not restricted to SVMs. Second, while the SVM+ solution contains twice the amount of parameters than the original SVM, the user can choose a priori the amount of parameters in the distilled classifier. Third, SVM+ learns the teacher correcting function and the student decision boundary simultaneously, but distillation proceeds sequentially: first with the teacher, then with the student. On the other hand, knowledge transfer is closer in spirit to distillation, but the two techniques differ: while similarity control relies on a student that purely imitates the hidden representation of a low-rank kernel machine, distillation is a trade-off between imitating soft predictions and hard labels, using arbitrary learning algorithms.

The framework of learning using privileged information enjoys theoretical analysis (Pechyony & Vapnik, 2010) and multiple applications, including ranking (Sharmanska et al., 2013), computer vision (Sharmanska et al., 2014; Lopez-Paz et al., 2014), clustering (Feyereisl & Aickelin, 2012), metric learning (Fouad et al., 2013), Gaussian process classification (Hernandez-Lobato et al., 2014),´ and finance (Ribeiro et al., 2010). Lapin et al. (2014) show that learning using privileged information is a particular instance of importance weighting.

## 4 GENERALIZED DISTILLATION

We now have all the necessary background to describe generalized distillation. To this end, consider the data $\{ ( x _ { i } , x _ { i } ^ { \star } , y _ { i } ) \} _ { i = 1 } ^ { n }$ . Then, the process of generalized distillation is as follows:

1. Learn teacher $f _ { t } \in \mathcal { F } _ { t }$ using the input-output pairs $\{ ( x _ { i } ^ { \star } , y _ { i } ) \} _ { i = 1 } ^ { n }$ and Eq. 3.

2. Compute teacher soft labels $\{ \sigma ( f _ { t } ( x _ { i } ^ { \star } ) / T ) \} _ { i = 1 } ^ { n }$ , using temperature parameter $T > 0$

3. Learn student $f _ { s } \in \mathcal { F } _ { s }$ using the input-output pairs $\{ ( x _ { i } , y _ { i } ) \} _ { i = 1 } ^ { n } , \{ ( x _ { i } , s _ { i } ) \} _ { i = 1 } ^ { n }$ , Eq. 4, and imitation parameter $\lambda \in [ 0 , 1 ] . ^ { 2 }$

We say that generalized distillation reduces to Hinton’s distillation if $x _ { i } ^ { \star } = x _ { i }$ for all $1 \leq i \leq n$ and $| \dot { \mathcal { F } } _ { s } | _ { \mathrm { C } } \ll | \mathcal { F } _ { t } | _ { \mathrm { C } }$ , where $| \cdot | _ { C }$ is an appropriate function class capacity measure. Conversely, we say that generalized distillation reduces to Vapnik’s learning using privileged information if $\boldsymbol { x } _ { i } ^ { \star }$ is a privileged description of $x _ { i }$ , and $| \mathcal { F } _ { s } | _ { \mathrm { C } } \gg | \mathcal { F } _ { t } | _ { \mathrm { C } }$ .

This comparison reveals a subtle difference between Hinton’s distillation and Vapnik’s privileged information. In Hinton’s distillation, $\mathcal { F } _ { t }$ is flexible, for the teacher to exploit her general purpose representation $x _ { i } ^ { \star } = x _ { i }$ to learn intricate patterns from large amounts of labeled data. In Vapnik’s privileged information, $\mathcal { F } _ { t }$ is simple, for the teacher to exploit her rich representation $x _ { i } ^ { \star } \neq x _ { i }$ to learn intricate patterns from small amounts of labeled data. The space of privileged information is thus a specialized space, one $\mathrm { o f } ^ { 6 6 }$ “metaphoric language”. In our running example of biopsy images, the space of medical reports is much more specialized than the space of pixels, since the space of pixels can also describe buildings, animals, and other unrelated concepts. In any case, the teacher must develop a language that effectively communicates information to help the student come up with better representations. The teacher may do so by incorporating invariances, or biasing them towards being robust with respect to the kind of distribution shifts that the teacher may expect at test time. In general, having a teacher is one opportunity to learn characteristics about the decision boundary which are not contained in the training sample, in analogy to a good Bayesian prior.

## 4.1 WHY DOES GENERALIZED DISTILLATION WORK?

Recall our three actors: the student function $f _ { s } \in \mathcal { F } _ { s } .$ the teacher function $f _ { t } \in \mathcal { F } _ { t }$ , and the real target function of interest to both the student and the teacher, $f \in { \mathcal { F } }$ . For simplicity, consider pure distillation (set the imitation parameter to $\lambda = 1 )$ . Furthermore, we will place some assumptions about how the student, teacher, and true function interplay when learning from n data. First, assume that the student may learn the true function at a slow rate

$$
R (f _ {s}) - R (f) \leq O \left(\frac {| \mathcal {F} _ {s} | _ {\mathrm{C}}}{\sqrt {n}}\right) + \varepsilon_ {s},
$$

where the $O ( \cdot )$ term is the estimation error, and $\varepsilon _ { s }$ is the approximation error of the student function class $\mathcal { F } _ { s }$ with respect to $f \in { \mathcal { F } }$ . Second, assume that the better representation of the teacher allows her to learn at the fast rate

$$
R (f _ {t}) - R (f) \leq O \left(\frac {| \mathcal {F} _ {t} | _ {\mathrm{C}}}{n}\right) + \varepsilon_ {t},
$$

where $\varepsilon _ { t }$ is the approximation error of the teacher function class $\mathcal { F } _ { t }$ with respect to $f \in { \mathcal { F } }$ . Finally, assume that when the student learns from the teacher, she does so at the rate

$$
R (f _ {s}) - R (f _ {t}) \leq O \left(\frac {| \mathcal {F} _ {s} | _ {\mathrm{C}}}{n ^ {\alpha}}\right) + \varepsilon_ {l},
$$

where $\varepsilon _ { l }$ is the approximation error of the student function class $\mathcal { F } _ { s }$ with respect to $f _ { t } \in \mathcal { F } _ { t } ,$ , and $\textstyle { \frac { 1 } { 2 } } \leq \alpha \leq 1$ . Then, the rate at which the student learns the true function $f$ admits the alternative expression

$$
\begin{array}{r l} & R (f _ {s}) - R (f) = R (f _ {s}) - R (f _ {t}) + R (f _ {t}) - R (f) \\ & \qquad \leq O \left(\frac {| \mathcal {F} _ {s} | _ {\mathrm{C}}}{n ^ {\alpha}}\right) + \varepsilon_ {l} + O \left(\frac {| \mathcal {F} _ {t} | _ {\mathrm{C}}}{n}\right) + \varepsilon_ {t} \\ & \qquad \leq O \left(\frac {| \mathcal {F} _ {s} | _ {\mathrm{C}} + | \mathcal {F} _ {t} | _ {\mathrm{C}}}{n ^ {\alpha}}\right) + \varepsilon_ {l} + \varepsilon_ {t}, \end{array}
$$

where the last inequality follows because $\alpha \leq 1$ . Thus, the question at hand is to argue, for a given learning problem, if the inequality

$$
O \left(\frac {| \mathcal {F} _ {s} | _ {\mathrm{C}} + | \mathcal {F} _ {t} | _ {\mathrm{C}}}{n ^ {\alpha}}\right) + \varepsilon_ {l} + \varepsilon_ {t} \leq O \left(\frac {| \mathcal {F} _ {s} | _ {\mathrm{C}}}{\sqrt {n}}\right) + \varepsilon_ {s}
$$

holds. The inequality highlights that the benefits of learning with a teacher arise due to i) the capacity of the teacher being small, ii) the approximation error of the teacher being smaller than the approximation error of the student, and iii) the coefficient α being greater than ${ \frac { 1 } { 2 } } .$ . Remarkably, these factors embody the assumptions of privileged information from Vapnik & Izmailov (2015). The inequality is also reasonable under the main assumption in (Hinton et al., 2015), which is $\varepsilon _ { s } \gg \varepsilon _ { t } + \varepsilon _ { l } .$ . Moreover, the inequality highlights that the teacher is most helpful in low data regimes, such as small datasets, Bayesian optimization, reinforcement learning, domain adaptation, transfer learning, or in the initial stages of online and reinforcement learning.

We believe that the $^ { \cdots } \alpha > { \frac { 1 } { 2 } } \ \mathrm { c a s e } ^ { 3 \prime }$ is a general situation, since soft labels (dense vectors with a real number of information per class) contain more information than hard labels (one-hot-encoding vectors with one bit of information per class) per example, and should allow for faster learning. This additional information, also understood as label uncertainty, relates to the acceleration in SVM+ due to the knowledge of slack values. Since a good teacher smoothes the decision boundary and instructs the student to fail on difficult examples, the student can focus on the remaining body of data. Although this translates into the unambitious “whatever my teacher could not do, I will not $\mathrm { d o } ^ { \prime \mathrm { 3 } }$ , the imitation parameter $\lambda \in [ 0 , 1 ]$ in (4) allows to follow this rule safely, and fall back to regular learning if necessary.

## 4.2 EXTENSIONS

Semi-supervised learning We now extend generalized distillation to the situation where examples lack regular features, privileged features, labels, or a combination of the three. In the following, we denote missing elements by . For instance, the example $( x _ { i } , \sqsubseteq , y _ { i } )$ has no privileged features, and the example $( x _ { i } , x _ { i } ^ { \star } , \bigsqcup )$ is missing its label. Using this convention, we introduce the clean subset notation

$$
c (S) = \{v: v \in S, v _ {i} \neq \square \forall i \}.
$$

Then, semi-supervised generalized distillation walks the same three steps as generalized distillation, enumerated at the beginning of Section 4, but uses the appropriate clean subsets instead of the whole data. For example, the semi-supervised extension of distillation allows the teacher to prepare soft labels for all the unlabeled data $\mathbf { \bar { \alpha } } c ( \{ ( x _ { i } , x _ { i } ^ { \star } ) \} _ { i = 1 } ^ { n } )$ . These additional soft-labels are additional information available to the student to learn the teacher representation $f _ { t }$

Learning with the Universum The unlabeled data $c ( \{ x _ { i } , x _ { i } ^ { \star } \} _ { i = 1 } ^ { n } )$ can belong to one of the classes of interest, or be Universum data (Weston et al., 2006; Chapelle et al., 2007). Universum data may have labels: in this case, one can exploit these additional labels by i) training a teacher that distinguishes amongst all classes (those of interest and those from the Universum), ii) computing soft class-probabilities only for the classes of interest, and iii) distilling these soft probabilities into a student function.

Learning from multiple tasks Generalized distillation applies to some domain adaptation, transfer learning, or multitask learning scenarios. On the one hand, if the multiple tasks share the same labels $y _ { i }$ but differ in their input modalities, the input modalities from the source tasks are privileged information. On the other hand, if the multiple tasks share the same input modalities $x _ { i }$ but differ in their labels, the labels from the source tasks are privileged information. In both cases, the regular student representation is the input modality from the target task.

Curriculum and reinforcement learning We conjecture that the uncertainty in the teacher soft predictions can be used as a mechanism to rank the difficulty of training examples, and use these ranks for curriculum learning (Bengio et al., 2009). Furthermore, distillation resembles imitation, a technique that learning agents could exploit in reinforcement learning environments.

## 4.3 A CAUSAL PERSPECTIVE ON GENERALIZED DISTILLATION

The assumption of independence of cause and mechanisms states that “the probability distribution of a cause is often independent from the process mapping this cause into its effects” (Scholkopf¨ et al., 2012). Under this assumption, for instance, causal learning problems —i.e., those where the features cause the labels— do not benefit from semi-supervised learning, since by the independence assumption, the marginal distribution of the features contains no information about the function mapping features to labels. Conversely, anticausal learning problems —those where the labels cause the features— may benefit from semi-supervised learning.

Causal implications also arise in generalized distillation. First, if the privileged features $x _ { i } ^ { \star }$ only add information about the marginal distribution of the regular features $x _ { i }$ , the teacher should be able to help only in anticausal learning problems. Second, if the teacher provides additional information about the conditional distribution of the labels $y _ { i }$ given the inputs x<sub>i</sub>, it should also help in the causal setting. We will confirm this hypothesis in the next section.

## 5 NUMERICAL SIMULATIONS

We now present some experiments to illustrate when the distillation of privileged information is effective, and when it is not. The necessary Python code to replicate all the following experiments is available at http://github.com/lopezpaz.

We start with four synthetic experiments, designed to minimize modeling assumptions and to illustrate different prototypical types of privileged information. These are simulations of logistic regression models repeated over 100 random partitions, where we use $n _ { \mathrm { t r } } = 2 0 0$ samples for training, and $n _ { \mathrm { t e } } = 1 0 , 0 0 0$ samples for testing. The dimensionality of the regular features $x _ { i }$ is $d = 5 0$ , and the involved separating hyperplanes $\bar { \boldsymbol { \alpha } } \in \mathbb { R } ^ { d }$ follow the distribution $\textstyle { \mathcal { N } } ( 0 , I _ { d } )$ . For each experiment, we report the test accuracy when i) using the teacher explanations $x _ { i } ^ { \star }$ at both train and test time, ii) using the regular features $x _ { i }$ at both train and test time, and iii) distilling the teacher explanations into the student classifier with $\lambda = T = 1$

1. Clean labels as privileged information. We sample triplets $( x _ { i } , x _ { i } ^ { \star } , y _ { i } )$ from:

$$
\begin{array}{l} x _ {i} \sim \mathcal {N} (0, I _ {d}) \\ x _ {i} ^ {\star} \leftarrow \langle \alpha , x _ {i} \rangle \\ \varepsilon_ {i} \sim \mathcal {N} (0, 1) \\ y _ {i} \leftarrow \mathbb {I} ((x _ {i} ^ {\star} + \varepsilon_ {i}) > 0). \end{array}
$$

Here, each teacher explanation $x _ { i } ^ { \star }$ is the exact distance to the decision boundary for each $x _ { i }$ , but the data labels $y _ { i }$ are corrupt. This setup aligns with the assumptions about slacks in the similarity control framework of Vapnik & Vashist (2009). We obtained a privileged test classification accuracy of $9 6 \pm 0 \%$ , a regular test classification accuracy of $8 8 \pm 1 \%$ , and a distilled test classification accuracy of $9 5 \pm { \bar { 1 } } \%$ . This illustrates that distillation of privileged information is an effective mean to detect outliers in label space.

2. Clean features as privileged information We sample triplets $( x _ { i } , x _ { i } ^ { \star } , y _ { i } )$ from:

$$
\begin{array}{l} x _ {i} ^ {\star} \sim \mathcal {N} (0, I _ {d}) \\ \varepsilon_ {i} \sim \mathcal {N} (0, I _ {d}) \\ x _ {i} \leftarrow x _ {i} ^ {\star} + \varepsilon \\ y _ {i} \leftarrow \mathbb {I} (\langle \alpha , x _ {i} ^ {\star} \rangle > 0). \end{array}
$$

In this setup, the teacher explanations $x _ { i } ^ { \star }$ are clean versions of the regular features $x _ { i }$ available at test time. We obtained a privileged test classification accuracy of $9 0 \pm { \mathrm { 1 \% } }$ , a regular test classification accuracy of $6 8 \pm 1 \%$ , and a distilled test classification accuracy of $7 0 \pm 1 \%$ . This improvement is not statistically significant. This is because the intelligent explanations $\boldsymbol { x } _ { i } ^ { \star }$ are independent from the noise $\varepsilon _ { i }$ polluting the regular features $x _ { i }$ . Therefore, there exists no additional information transferable from the teacher to the student.

3. Relevant features as privileged information We sample triplets $( x _ { i } , x _ { i } ^ { \star } , y _ { i } )$ from:

$$
\begin{array}{l} x _ {i} \sim \mathcal {N} (0, I _ {d}) \\ x _ {i} ^ {\star} \leftarrow x _ {i, J} \\ y _ {i} \leftarrow \mathbb {I} (\langle \alpha_ {J}, x _ {i} ^ {\star} \rangle > 0), \end{array}
$$

where the set $^ { J , }$ with $\left| J \right| = 3 ,$ is a subset of the variable indices $\{ 1 , \ldots , d \}$ chosen at random but common for all samples. In another words, the teacher explanations indicate the values of the variables relevant for classification, which translates into a reduction of the dimensionality of the data that we have to learn from. We obtained a privileged test classification accuracy of $9 8 \pm 0 \% ,$ a regular test classification accuracy of $8 9 \pm 1 \%$ , and a distilled test classification accuracy of $9 7 \pm 1 \%$ This illustrates that distillation on privileged information is an effective tool for feature selection.

4. Sample-dependent relevant features as privileged information Sample triplets

$$
\begin{array}{l} x _ {i} \sim \mathcal {N} (0, I _ {d}) \\ x _ {i} ^ {\star} \leftarrow x _ {i, J _ {i}} \\ y _ {i} \leftarrow \mathbb {I} (\langle \alpha_ {J _ {i}}, x _ {i} ^ {\star} \rangle > 0), \end{array}
$$

where the sets $J _ { i } ,$ with $| J _ { i } | = 3$ for all $i ,$ are a subset of the variable indices $\{ 1 , \ldots , d \}$ chosen at random for each sample $\boldsymbol { x } _ { i } ^ { \star }$ . One interpretation of such model is the one of bounding boxes in computer vision: each high-dimensional vector $x _ { i }$ would be an image, and each teacher explanation $\boldsymbol { x } _ { i } ^ { \star }$ would be the pixels inside a bounding box locating the concept of interest (Sharmanska et al., 2013). We obtained a privileged test classification accuracy of $9 6 \pm 2 \%$ , a regular test classification accuracy of $5 5 \pm 3 \%$ , and a distilled test classification accuracy of $0 . 5 6 \pm 4 \%$ . Note that although the classification is linear in $x ^ { \star }$ , this is not the case in terms of $x .$ Therefore, although we have misspecified the function class $\mathcal { F } _ { s }$ for this problem, the distillation approach did not deteriorate the final performance.

The previous four experiments set up causal learning problems. In the second experiment, the privileged features $\boldsymbol { x } _ { i } ^ { \star }$ add no information about the target function mapping the regular features to the labels, so the causal hypothesis from Section 4.3 justifies the lack of improvement. The first and third experiments provide privileged information that adds information about the target function, and therefore is beneficial to distill this information. The fourth example illustrates that the privileged features adding information about the target function is not a sufficient condition for improvement.

![](images/2a0b0173ed706ab2df31e99aa2abf350c17bdaf141b67e55826c49200b68be82.jpg)

![](images/39534c20116c2efce09b2ff00f90270ae434473bef07116dfc6bc90ff2761fe9.jpg)

Figure 1: Results on MNIST for 300 samples (left) and 500 samples (right).  
![](images/e103c203efc3775e361dccae3af294aaa4a660ea57bb70772f73a46d0cfbb4a4.jpg)

![](images/41f68982d11bed90e6bd0143729b2349d3e83a887374ee6ff336dad874da0ea9.jpg)  
Figure 2: Results on CIFAR 10 (left) and SARCOS (right).

5. MNIST handwritten digit image classification The privileged features are the original 28x28 pixels MNIST handwritten digit images (LeCun et al., 1998b), and the regular features are the same images downscaled to 7x7 pixels. We use 300 or 500 samples to train both the teacher and the student, and test their accuracies at multiple levels of temperature and imitation on the full test set. Both student and teacher are neural networks of composed by two hidden layers of 20 rectifier linear units and a softmax output layer (the same networks are used in the remaining experiments). Figure 1 summarizes the results of this experiment, where we see a significant improvement in classification accuracy when distilling the privileged information, with respect to using the regular features alone. As expected, the benefits of distillation diminished as we further increased the sample size.

6. Semisupervised learning We explore the semisupervised capabilities of generalized distillation on the CIFAR10 dataset (Krizhevsky, 2009). Here, the privileged features are the original 32x32 pixels CIFAR10 color images, and the regular features are the same images when polluted with additive Gaussian noise. We provide labels for 300 images, and unlabeled privileged and regular features for the rest of the training set. Thus, the teacher trains on 300 images, but computes the soft labels for the whole training set of 50, 000 images. The student then learns by distilling the 300 original hard labels and the 50, 000 soft predictions. As seen in Figure 2, the soft labeling of unlabeled data results in a significant improvement with respect to pure student supervised classification. Distillation on the 300 labeled samples did not improve the student performance. This illustrates the importance of semisupervised distillation in this data. We believe that the drops in performance for some distillation temperatures are due to the lack of a proper weighting between labeled and unlabeled data in (4).

7. Multitask learning The SARCOS dataset (Vijayakumar, 2000) characterizes the 7 joint torques of a robotic arm given 21 real-valued features. Thus, this is a multitask learning problem, formed by 7 regression tasks. We learn a teacher on 300 samples to predict each of the 7 torques given the other 6, and then distill this knowledge into a student who uses as her regular input space the 21 real-valued features. Figure 2 illustrates the performance improvement in mean squared error when using generalized distillation to address the multitask learning problem. When distilling at the proper temperature, distillation allowed the student to match her teacher performance.

## ACKNOWLEDGMENTS

We thank discussions with R. Nishihara, R. Izmailov, I. Tolstikhin, and C. J. Simon-Gabriel.

## REFERENCES

Ba, Jimmy and Caruana, Rich. Do deep nets really need to be deep? In NIPS, 2014.

Bengio, Yoshua, Louradour, Jer´ ome, Collobert, Ronan, and Weston, Jason. Curriculum learning. Inˆ ICML, 2009.

Bottou, Leon. From machine learning to machine reasoning.´ Machine learning, 94(2):133–149, 2014.

Bucilua, Cristian, Caruana, Rich, and Niculescu-Mizil, Alexandru. Model compression. In ˇ KDD, 2006.

Burges, Christopher and Scholkopf, Bernhard. Improving the accuracy and speed of support vector¨ learning machines. In NIPS, 1997.

Chapelle, Olivier, Agarwal, Alekh, Sinz, Fabian H, and Scholkopf, Bernhard. An analysis of infer-¨ ence with the Universum. In NIPS, 2007.

Feyereisl, Jan and Aickelin, Uwe. Privileged information for data clustering. Information Sciences, 194:4–23, 2012.

Fouad, Shereen, Tino, Peter, Raychaudhury, Somak, and Schneider, Petra. Incorporating privileged information through metric learning. Neural Networks and Learning Systems, 24(7):1086–1098, 2013.

Hernandez-Lobato, Daniel, Sharmanska, Viktoriia, Kersting, Kristian, Lampert, Christoph H, and´ Quadrianto, Novi. Mind the nuisance: Gaussian process classification using privileged noise. In NIPS, 2014.

Hinton, Geoffrey, Vinyals, Oriol, and Dean, Jeff. Distilling the knowledge in a neural network. arXiv, 2015.

Krizhevsky, Alex. The CIFAR-10 and CIFAR-100 datasets, 2009. URL http://www.cs. toronto.edu/ kriz/cifar.html.

Lapin, Maksim, Hein, Matthias, and Schiele, Bernt. Learning using privileged information: Svm+ and weighted svm. Neural Networks, 53:95–108, 2014.

LeCun, Yann, Bottou, Leon, Bengio, Yoshua, and Haffner, Patrick. Gradient-based learning applied ´ to document recognition. Proceedings ofthe IEEE, 86(11):2278–2324, 1998a.

LeCun, Yann, Cortes, Corinna, and Burges, Christopher JC. The MNIST database of handwritten digits, 1998b. URL http://yann.lecun.com/exdb/mnist/.

Lopez-Paz, David, Sra, Suvrit, Smola, Alex, Ghahramani, Zoubin, and Scholkopf, Bernhard. Ran-¨ domized nonlinear component analysis. In ICML, 2014.

Mikolov, Tomas, Chen, Kai, Corrado, Greg, and Dean, Jeffrey. Efficient estimation of word representations in vector space. arXiv, 2013.

Oquab, Maxime, Bottou, Leon, Laptev, Ivan, and Sivic, Josef. Learning and transferring mid-level image representations using convolutional neural networks. In CVPR, pp. 1717–1724, 2014.

Pechyony, Dmitry and Vapnik, Vladimir. On the theory of learning with privileged information. In NIPS, 2010.

Ribeiro, Bernardete, Silva, Catarina, Vieira, Armando, Gaspar-Cunha, Antonio, and das Neves,´ Joao C. Financial distress model prediction using SVM+. In˜ IJCNN. IEEE, 2010.

Scholkopf, Bernhard, Janzing, Dominik, Peters, Jonas, Sgouritsa, Eleni, Zhang, Kun, and Mooij,¨ Joris. On causal and anticausal learning. ICML, 2012.

Sharmanska, Viktoriia, Quadrianto, Novi, and Lampert, Christoph H. Learning to rank using privileged information. In ICCV, 2013.

Sharmanska, Viktoriia, Quadrianto, Novi, and Lampert, Christoph H. Learning to transfer privileged information. arXiv, 2014.

Vapnik, Vladimir. Statistical learning theory. Wiley New York, 1998.

Vapnik, Vladimir and Izmailov, Rauf. Learning using privileged information: Similarity control and knowledge transfer. JMLR, 16:2023–2049, 2015.

Vapnik, Vladimir and Vashist, Akshay. A new learning paradigm: Learning using privileged information. Neural Networks, 22(5):544–557, 2009.

Vijayakumar, Sethu. The SARCOS dataset, 2000. URL http://www.gaussianprocess. org/gpml/data/.

Weston, Jason, Collobert, Ronan, Sinz, Fabian, Bottou, Leon, and Vapnik, Vladimir. Inference with´ the Universum. In ICML, 2006.