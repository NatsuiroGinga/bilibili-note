---
title: "2023-Zhang-LLaMA-Adapter"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "pinn"
source_pdf: "raw/papers/pinn/2023-Zhang-LLaMA-Adapter.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# LLAMA-ADAPTER: EFFICIENT FINE-TUNING OF LARGE LANGUAGE MOD-ELS WITH ZERO-INITIALIZED ATTENTION

Renrui Zhang<sup>∗1,2</sup>, Jiaming Han<sup>∗1,2</sup>, Chris Liu<sup>∗1</sup>, Aojun Zhou<sup>2</sup>, Pan Lu<sup>3</sup> Yu Qiao<sup>†1</sup>, Hongsheng Li<sup>†2,4</sup>, Peng Gao<sup>†‡∗1</sup>

<sup>1</sup>Shanghai Artificial Intelligence Laboratory <sup>2</sup>CUHK MMLab

<sup>3</sup>University of California, Los Angeles <sup>4</sup>CPII of InnoHK

{zhangrenrui, hanjiaming, gaopeng, qiaoyu}@pjlab.org.cn hsli@ee.cuhk.edu.hk

## ABSTRACT

With the rising tide of large language models (LLMs), there has been a growing interest in developing general-purpose instruction-following models, e.g., Chat GPT. To this end, we present LLaMA-Adapter, a lightweight adaption method for efficient instruction tuning of LLaMA. Using 52K self-instruct demonstrations, LLaMA-Adapter only introduces 1.2M learnable parameters upon the frozen LLaMA 7B model, and costs less than one hour for fine-tuning. Specifically, a zero-initialized attention mechanism is proposed. It adopts a learnable zero gating to adaptively inject the instructional cues into LLaMA within self-attention layers, contributing to a stable training process and superior final performance. In this way, LLaMA-Adapter can generate high-quality responses to diverse language instructions, comparable to Alpaca with fully fine-tuned 7B parameters. Besides language commands, by incorporating an image encoder, our approach can be simply extended to a Multi-modal LLM for image-conditioned instruction following, which achieves superior multi-modal reasoning capacity on several popular benchmarks (MME, MMBench, LVLM-eHub). Furthermore, we also verify the proposed zero-initialized attention mechanism for fine-tuning other pre-trained models (ViT, RoBERTa, CLIP) on traditional vision and language tasks, demonstrating the effectiveness and generalizability of our approach. Code and models are released at https://github.com/OpenGVLab/LLaMA-Adapter.

## 1 INTRODUCTION

Large Language Models (LLMs) (Dai et al., 2019; Radford et al., 2019; Zhang et al., 2022; Raffel et al., 2020; Devlin et al., 2018) have stimulated widespread attention in both academia and industry. Driven by massive corpora and advanced hardware, LLMs exhibit remarkable understanding and generative ability, propelling language tasks to a higher level. Recently, significant progress has been made on instruction-following models, e.g., ChatGPT (OpenAI, 2023a) and GPT-4 (OpenAI, 2023b), which follow language instructions and generate contextual responses. However, the further prevalence of instruction models is largely impeded by the closed-source restriction and high development costs.

To alleviate this, Stanford Alpaca (Taori et al., 2023) proposes to fine-tune an open-source LLM, i.e., LLaMA (Touvron et al., 2023) into an instruction-following model, which is affordable and replicable. Starting from 175 human-written instruction-output pairs (Wang et al., 2022a), Alpaca leverages GPT-3.5 (Brown et al., 2020) to expand the training data to 52K in a self-instruct manner. Supervised by this, Alpaca fine-tunes the entire 7B parameters in LLaMA, producing an exceptional instruction model that performs similarly to GPT-3.5. Despite Alpaca’s effectiveness, a complete fine-tuning of large-scale LLaMA is still time-consuming, computation-intensive, and cumbersome to transfer to different downstream scenarios.

![](images/f44986d3bd54eb7dbbd37de71035c179b8d4744a8f340e1746112d0ea92bb95f.jpg)  
Figure 1: Characteristics of LLaMA-Adapter. Our lightweight adaption method efficiently finetunes LLaMA (Touvron et al., 2023) 7B model with only 1.2M learnable parameters within one hour, which exhibits superior instruction-following and multi-modal reasoning capacity.

In this paper, we introduce LLaMA-Adapter, an efficient fine-tuning method that adapts LLaMA into a well-performed instruction-following model. Trained by Alpaca’s instruction-output data, our approach freezes the entire LLaMA model, and proposes a zero-initialized attention mechanism with superior resource efficiency. Specifically, in LLaMA’s higher transformer layers, we append a set of learnable adaption prompts as prefixes to the word tokens. Then, to avoid the noise from randomly initialized prompts at the early training stage, we equip the frozen self-attention layers with a learnable gating factor. The gating mechanism is initialized by zeros, and controls the feature interaction between prompt and word tokens, within the process of attention calculation. Such a strategy can first preserve the original knowledge in LLaMA, and progressively inject the new instructional signals during training. This contributes to a more stable learning process and better instruction-following capacity of the final model.

Overall, our LLaMA-Adapter exhibits four main characteristics, as shown in Figure 1.

• 1.2M Parameters. Instead of updating the full 7B parameters, we freeze the pre-trained LLaMA and only learn the zero-initialized attention mechanism with 1.2M parameters. This, however, reveals comparable instruction-following proficiency with the 7B Alpaca.

• One-hour Fine-tuning. Thanks to our lightweight adaption modules with zero-initialized gating, the training convergence of LLaMA-Adapter costs less than one hour on 8 A100 GPUs, which are three times faster than Alpaca.

• Plug with Expertise. For different scenarios, it is flexible to insert their respective adapters to endow LLaMA with different expert knowledge or new modality input. Thus, it suffices to store a 1.8M adapter within each context, other than a complete copy of the 13G LLaMA.

• Multi-modal Reasoning. Besides language instruction, our approach can also incorporate an image encoder via zero-initialized attention to become a multi-modal LLM. Compared to concurrent works (Liu et al., 2023b; Zhu et al., 2023), LLaMA-Adapter showcases higher tuning efficiency with competitive reasoning capacity on MME (Fu et al., 2023), MMBench (Liu et al., 2023c), and LVLM-eHub (Xu et al., 2023) benchmarks.

In addition to instruction tuning, our zero-initialized attention can be generalized to traditional vision and language tasks for parameter-efficient fine-tuning. We apply our approach to the pretrained ViT (Dosovitskiy et al., 2020), ReBERTa (Liu et al., 2019), and CLIP (Radford et al., 2021), respectively for fine-tuning vision, language, and vision-language models. On a wide range of downstream tasks, we demonstrate the effectiveness of our proposed method for traditional tasks.

## 2 RELATED WORK

Instruction Tuning of Language Models. The subfield of language models learning instructionfollowing capabilities aims to generate responses based on natural language commands. These methods normally enhance the pre-trained LLMs by fine-tuning them with high-quality instructionoutput data pairs. Early works, such as FLAN (Wei et al., 2021), PromptSource (Bach et al.,

2022), and SUP-NATINST (Wang et al., 2022b), introduce effective instruction tuning methods and establish comprehensive evaluation benchmarks. InstructGPT (Ouyang et al., 2022) demonstrates significant improvement in the instruction-following power, but is closed-source to the community. To promote the open source of instruction models, Stanford Alpaca (Taori et al., 2023) fine-tunes all the 7B parameters of LLaMA (Touvron et al., 2023) with 52K self-instruct data. However, this full-model fine-tuning can be inefficient in both time and computation resources, limiting its transferability to downstream applications. In this paper, we propose LLaMA-Adapter to fine-tune only lightweight zero-initialized attention mechanisms on top of the frozen LLaMA, other than updating parameters of the entire model. There are several works concurrent to ours, Alpaca-LoRA (alp, 2023), Vicuna (Chiang et al., 2023), and LLaMA-GPT4 (Peng et al., 2023), which aim to improve Alpaca from different aspects. Alpaca-LoRA utilizes the existing LoRA (Hu et al., 2021) to efficiently fine-tune LLaMA, which is restricted to the original network structure and cannot be extended for image input. In contrast, our LLaMA-Adapter achieves higher training efficiency and can be simply generalized to a multi-modal LLM via zero-initialized attention. Vicuna and LLaMA-GPT4 target at constructing a more advanced instruction dataset using ChatGPT (OpenAI, 2023a) and GPT-4 (OpenAI, 2023b), instead of Alpaca’s 52K data, which still adopt full fine-tuning without the potential for multi-modal instruction tuning.

Parameter-efficient Fine-tuning. The pre-training and fine-tuning paradigms have been proven to be highly effective in different language and vision tasks. Compared to full fine-tuning, Parameter-Efficient Fine-Tuning (PEFT) (Paul, 2022) methods freeze most parameters of pre-trained models, and aim to exhibit comparable capabilities on downstream tasks (Wang et al., 2018; Puzikov & Gurevych, 2018). Therein, prompt tuning appends a collection of trainable tokens to pre-trained large models, which are inserted either to the input embeddings (Lester et al., 2021; Liu et al., 2021b) or every intermediate layer (Li & Liang, 2021; Liu et al., 2021a). LoRA (Hu et al., 2021; Zhang et al., 2023d; Hedegaard et al., 2022) introduces trainable rank decomposition matrices into each network weights (Karimi Mahabadi et al., 2021), indicating promising fine-tuning ability on large generative models (Cuenca & Paul, 2023; alp, 2023). Adapters (Houlsby et al., 2019) insert lightweight adaption modules into each block of the transformer and have been extended across numerous domains (Gesmundo & Dean, 2022; Gao et al., 2021; Zhang et al., 2021). Different from previous efforts, we propose the LLaMA-Adapter with zero-initialized attention specially designed for instruction tuning and multi-modal reasoning of LLaMA (Touvron et al., 2023). Some existing works also adopt gating techniques in prompt tuning (Yoo et al., 2023; Goswami et al., 2023), but conduct a naive gated combination of different prompt tokens with randomly initialized factors. Instead, our gating factor learns from zero during training, and is delicately integrated into self-attention layers. Another branch of work applies zero initialization to convolutional networks (Zhao et al., 2021), text-to-image diffusion models (ControlNet (Zhang et al., 2023c)), or vision-language learning (Flamingo (Alayrac et al., 2022)). They are not PEFT methods requiring large-scale parameters, and have motivations for better network-level initialization or feature-level fusion via residual connections, very different from our interaction controlling within attention layers.

## 3 LLAMA-ADAPTER

In Section 3.1, we first introduce to insert learnable adaption prompts into LLaMA’s (Touvron et al., 2023) transformer. Then, we present the details of zero-initialized attention mechanisms with zero gating in Section 3.2, and generalize LLaMA-Adapter for multi-modal reasoning in Section 3.3. Finally, we extend our approach for efficient fine-tuning of language and vision models in Section ??.

## 3.1 LEARNABLE ADAPTION PROMPTS

Given a pre-trained LLaMA with an N-layer transformer, we first insert a set of learnable adaption prompts into its topmost L layers $( L \leq N )$ . We denote the prompts as $\{ P _ { l } \} _ { l = 1 } ^ { L }$ , where $P _ { l } \in \mathbb { R } ^ { \mathbf { \dot { K } } \times C }$ with K denoting the prompt length for each layer, and C equaling the feature dimension of LLaMA’s transformer. The prompting at last L layers can better tune the language representations with higher-level semantics.

Taking the l-th inserted layer as an example $( l \ \leq \ L )$ , we denote the M-length word tokens as $T _ { l } \in \breve { \mathbb { R } } ^ { M \times C }$ , which represent the input instruction and the already generated response. The learnable adaption prompt is concatenated with $T _ { l }$ along the token dimension as prefixes, formulated as

$$
[ P _ {l}; T _ {l} ] \in \mathbb {R} ^ {(K + M) \times C}.\tag{1}
$$

In this way, the instruction knowledge learned within $P _ { l } .$ , can effectively guide $T _ { l }$ to generate the subsequent contextual response via our zero-initialized attention layers in the transformer block.

## 3.2 ZERO-INITIALIZED ATTENTION

If the adaption prompts are randomly initialized, they might bring disturbance to the word tokens at the beginning of training, which harms the fine-tuning stability and effectiveness. Consider ing this, we modify the vanilla self-attention at the last $L$ layers to be zero-initialized variants, as shown in Figure 2. Suppose the model is generating the $( \bar { M } + 1 )$ -th word on top of $[ P _ { l } ; T _ { l } ]$ at the l-th inserted layer, we denote the corresponding $( M + 1 )$ -th word token as $t _ { l } \in \mathbb { R } ^ { 1 \times C }$ In the attention mechanism, several linear projection layers are first applied to transform the input tokens into queries, keys, and values as

$$
Q _ {l} = \mathrm{Linear} _ {\mathrm{q}} (t _ {l});\tag{2}
$$

$$
K _ {l} = \operatorname{Linear} _ {\mathrm{k}} \left(\left[ P _ {l}; T _ {l}; t _ {l} \right]\right);\tag{3}
$$

![](images/d6d220b7a502ad5904b8f79a46bfb7c4bdddaea96653de169d3b320885832684.jpg)

$$
V _ {l} = \operatorname{Linear} _ {\mathrm{v}} ([ P _ {l}; T _ {l}; t _ {l} ]).\tag{4}
$$

Then, the attention scores of $Q _ { l }$ and $K _ { l }$ before the softmax function are calculated as

$$
S _ {l} = Q _ {l} K _ {l} ^ {T} / \sqrt {C} \in \mathbb {R} ^ {1 \times (K + M + 1)},\tag{5}
$$

which records the feature similarities between the new word $t _ { l }$ and all $K + M + 1$ tokens. Meanwhile, $S _ { l }$ can be reformulated by two components as

$$
S _ {l} = [ S _ {l} ^ {K}; S _ {l} ^ {M + 1} ] ^ {T},\tag{6}
$$

where $S _ { l } ^ { K } \in \mathbb { R } ^ { K \times 1 }$ and $S _ { I } ^ { M + 1 } \in \mathbb { R } ^ { ( M + 1 ) \times 1 }$ denote the attention scores of $K$ adaption prompts and $M + 1$ word tokens, respectively. The for-

Figure 2: Details of Zero-initialized Attention. We insert learnable adaption prompts into the last L out of $N$ transformer layers of LLaMA. To progressively learn the instructional knowledge, we adopt a zero gating factor within the attention for stable training in the early training stages.

mer $S _ { l } ^ { K }$ represents how much information the learnable prompt contributes to generating $t _ { l } ,$ which probably causes disturbance in the early training stage.

To this end, we adopt a learnable gating factor, denoted as $g _ { l } .$ , to adaptively control the importance of $S _ { l } ^ { K }$ in the attention. Initialized by zero, $g _ { l }$ can firstly eliminate the influence of under-fitted prompts, and then increase its magnitude for providing more instruction semantics to LLaMA. Therefore, we independently apply the softmax functions to the two components in Equation equation $^ { 6 , }$ and multiply the first term by $g _ { l }$ , formulated as

$$
S _ {l} ^ {g} = [ \operatorname{softmax} (S _ {l} ^ {K}) \cdot \tanh (g _ {l}); \operatorname{softmax} (S _ {l} ^ {M + 1}) ] ^ {T},\tag{7}
$$

where an activation function tan $\iota ( \cdot )$ is adopted to regulate the scale of $g _ { l }$ to into -1∼1. The separate softmax functions ensure the second term to be irrelevant to the adaption prompts, and we do not multiply any coefficient to softmax $( S _ { l } ^ { M + 1 } )$ to prevent the pre-trained knowledge from being disturbed, i.e., preserving its original probability distribution. When $g _ { l }$ is close to zero, it can mostly convey the originally pre-trained knowledge of LLaMA to token $t _ { l }$ for a creditable generation. In practice, we adopt multiple $g _ { l }$ to be independently learned for different heads within the attention, benefiting the learning diversity of multi-head mechanisms.

Finally, we calculate the output of the l-th attention layer with a linear projection layer as

$$
t _ {l} ^ {o} = \mathrm{Linear} _ {\mathrm{o}} (S _ {l} ^ {g} V _ {l}) \in \mathbb {R} ^ {1 \times C}.\tag{8}
$$

With our proposed zero-initialized attention, the adaption prompts can progressively inject the newly acquired instructional signals into the transformer, while simultaneously incorporating the pre-trained knowledge of LLaMA to provide high-quality responses.

![](images/f56c53ec9aa79dce4335eb5ee68d307326173ba788f69430b11ff0c12c9b3ea2.jpg)  
Figure 3: Multi-modal LLaMA-Adapter. By connecting a pre-trained image encoder, LLaMA-Adapter can be extended to a multi-modal LLM for image-conditioned instruction following. Given an image input, we element-wisely add the image tokens with adaption prompts, and utilize our zero-initialized attention mechanism to inject visual semantics into LLaMA (Touvron et al., 2023).

## 3.3 MULTI-MODAL REASONING

Apart from language instructions, LLaMA-Adapter is capable of answering a question based on image input with simple modifications. This fully unleashes the multi-modal reasoning power of LLMs for extensive application scenarios, e.g., image captioning, object counting, and OCR. The overall framework of our multi-modal LLaMA-Adapter is shown in Figure 3.

Multi-modal Architecture. For an input image, we first leverage a pre-trained visual encoder, e.g., CLIP (Radford et al., 2021), to extract its multi-scale global features, denoted as $\lbrace I _ { m } \rbrace _ { m = 1 } ^ { M }$ , where $I _ { m } \in \dot { \mathbb { R } } ^ { 1 \times C _ { m } }$ and M denotes the scale number. Then, we concatenate the M-scale features along the channel dimension, and apply a learnable projection network to transform them into word embedding space, formulated as

$$
I _ {p} = \text { Projection } \left(\text { Concat } \left(\{I _ {m} \} _ {m = 1} ^ {M}\right)\right),\tag{9}
$$

where $I _ { p } \in \mathbb { R } ^ { 1 \times C }$ and is regarded as the overall image token with the same feature dimension as our adaption prompts. After this, we repeat $I _ { p }$ for K times, and element-wisely add it onto the K-length adaption prompts at all L inserted transformer layers. For the l-th layer, we denote the acquired multi-modal prompt as

$$
P _ {l} ^ {v} = P _ {l} + \mathrm{Repeat} (I _ {p}) \in \mathbb {R} ^ {K \times C},\tag{10}
$$

where $P _ { l } ^ { v }$ denotes the prompt incorporating visual information from the given image. After this, our zero-initialized attention can learn to increasingly infuse the image-conditional semantics into LLaMA by the zero gating factor g . In this way, an LLM can be efficiently tuned to understand vision-language input, and tackle more challenging generative tasks with multi-modal reasoning.

Training Strategy. Instead of using Alpaca’s data (Taori et al., 2023) for language-only instruction tuning, we fine-tune LLaMA-Adapter with multi-modal instruction data, and evaluate the performance with two popular scenarios:

• ScienceQA (Lu et al., 2022) Evaluation. ScienceQA includes a large-scale science question answering data collected from a wide range of knowledge domains. Each sample contains a visual context, a textual context, a question with multiple options, and an answer. We directly utilize ScienceQA’s multi-modal training set to fine-tune LLaMA-Adapter, and conduct in-domain testing. We freeze both the image encoder and LLaMA, and only train the lightweight projection network and zero-initialized attention mechanisms.

• Zero-shot Multi-modal Evaluation. To verify the out-of-domain generation ability of our approach, we conduct a two-stage multi-modal training, and then evaluate three benchmarks (MME (Fu et al., 2023), MMBench (Liu et al., 2023c), LVLM-eHub (Xu et al., 2023))

```txt
Instruction: Tell me about alpacas.

Alpaca: Alpacas are small, fluffy animals related to camels and llamas. They are native to Peru and Bolivia, and were first domesticated around 5,000 years ago. They are kept mainly for their fine, soft fleece, which is used to make knitwear and other garments. Alpacas are herd animals and live in small family groups. They are highly social animals and can form strong bonds with their owners.

LLaMA-Adapter: Alpacas are members of the camelid family and are native to the Andes Mountains of South America. They are typically found in herds of 10-20 animals and are known for their gentle nature and their ability to thrive in harsh climates. Alpacas are typically white or grey in color and have long, silky coats. They are also known for their ability to produce high-quality wool, which is used in the production of clothing and other products.

Instruction: Translate the sentence 'I have no mouth but I must scream' into Spanish.

Alpaca: No tengo boca, pero debo gritar.

LLaMA-Adapter: No tengo boca pero tengo que gritar.

Instruction: Write a Python program that prints the first 10 Fibonacci numbers.

Alpaca:
numbers = [0, 1]
for i in range(2, 11):
    numbers.append(numbers[i-2] + numbers[i-1])
print(numbers)

LLaMA-Adapter:
def print_fibonacci(n):
    a, b = 0, 1
    count = 0
    while count < n:
    print(a, end=' ') 
    a, b = b, a + b
    count += 1
print_fibonacci(10)
```  
Figure 4: Language Instruction-following Capacity. Our LLaMA-Adapter performs comparably with Alpaca (Taori et al., 2023) for question answering, language translation, and code generation.

in a zero-shot manner. For the first stage, we utilize the raw image-caption data from LAION-400M (Schuhmann et al., 2021) to tune the projection network and zero-initialized attention modules. This step is mainly for the alignment of embedding space between visual features and word tokens. For the second stage, we freeze the projection network, and only tune the zero-initialized attention within LLaMA by a combination of Alpaca’s data and LLaVA-I (Liu et al., 2023b). The second stage aims to endow LLMs with the capability to generate detailed responses based on human instructions.

## <sup>batch</sup> <sup>size,</sup> <sup>learning</sup> <sup>r</sup>4 EXPERIMENT

quantitative results, we compare with methods both trained by the 52K instruction data, Alpaca (Taori<sup>In</sup> <sup>Section</sup> <sup>4.1,</sup> <sup>we</sup> <sup>first</sup> <sup>evaluate</sup> <sup>the</sup> <sup>language</sup> <sup>instruction-following</sup> <sup>capacity</sup> <sup>of</sup> <sup>LLaMA-Adapter.</sup> et al., 2023) and Alpaca-LoRA (alp, 2023), and evaluate with one widely adopted schemes, GPT-4Then, we present our multi-modal reasoning performance on several benchmarks in Section 4.2, evaluating benchmark (Chiang et al., 2023). It adopts GPT-4 (OpenAI, 2023b) to assess the qualityand conduct ablation studies on ScienceQA’s validation set in Section 4.3. Finally, we report the of two compared responses from different models on 80 questions.fine-tuning results of our approach on traditional vision and language models in Section 4.4.

## Performance. We first show some generated res4.1 I<sub>NSTRUCTION</sub>-<sub>FOLLOWING</sub> E<sub>VALUATION</sub>

fully fine-tuned Alpaca, including question answering, language translation, and code generation.Settings. Following Stanford Alpaca (Taori et al., 2023), we utilize 52K instruction-following data for training. We fine-tune LLaMA-Adapter on 8 A100 GPUs for 5 epochs. The warmup epochs, batch size, learning rate, and weight decay are set to 2, 64, 0.009, and 0.02, respectively. By default, we utilize the pre-trained LLaMA model with 7B parameters and N = 32 transformer layers. We

![](images/285e4702171e0b743002a67aba281a4529420a68f4fa2e327835ee21d93f01e0.jpg)  
Figure 5: GPT-4 Evaluating Benchmark (Chiang et al., 2023) for LLaMA-Adapter, Alpaca and Alpaca-LoRA.

Ours vs. Alpaca-LoRA

Table 1: Efficiency Comparison. The training time is tested on 8 A100 GPUs.

<table><tr><td>Model</td><td>Tuned Params</td><td>Storage Space</td><td>Training Time</td></tr><tr><td>Alpaca</td><td>7B</td><td>13G</td><td>3 hours</td></tr><tr><td>Alpaca-LoRA</td><td>4.2M</td><td>16.8M</td><td>1.5 hours</td></tr><tr><td>LLaMA-Adapter</td><td>1.2M</td><td>4.7M</td><td>1 hour</td></tr></table>

Table 2: Visual Question Answering on ScienceQA (Lu et al., 2022) Benchmark. CoT denotes using a chain of thought for question answering. T denotes using text-only input.

<table><tr><td>Model</td><td>Tuned Params</td><td>Avg</td><td>NAT</td><td>SOC</td><td>LAN</td><td>TXT</td><td>IMG</td><td>NO</td><td>G1-6</td><td>G7-12</td></tr><tr><td>Random Choice (Lu et al., 2022)</td><td>-</td><td>39.83</td><td>40.28</td><td>46.13</td><td>29.25</td><td>47.45</td><td>40.08</td><td>33.66</td><td>39.35</td><td>40.67</td></tr><tr><td>Human (Lu et al., 2022)</td><td>-</td><td>88.40</td><td>90.23</td><td>84.97</td><td>87.48</td><td>89.60</td><td>87.50</td><td>88.10</td><td>91.59</td><td>82.42</td></tr><tr><td>ChatGPT $_{CoT}$  (OpenAI, 2023a)</td><td>0M</td><td>78.31</td><td>78.82</td><td>70.98</td><td>83.18</td><td>77.37</td><td>67.92</td><td>86.13</td><td>80.72</td><td>74.03</td></tr><tr><td>GPT-4 $_{CoT}$  (OpenAI, 2023b)</td><td>0M</td><td>83.99</td><td>85.48</td><td>72.44</td><td>90.27</td><td>82.65</td><td>71.49</td><td>92.89</td><td>86.66</td><td>79.04</td></tr><tr><td>MCAN (Yu et al., 2019)</td><td>95M</td><td>54.54</td><td>56.08</td><td>46.23</td><td>58.09</td><td>59.43</td><td>51.17</td><td>55.40</td><td>51.65</td><td>59.72</td></tr><tr><td>VisualBERT (Li et al., 2019a; 2020)</td><td>111M</td><td>61.87</td><td>59.33</td><td>69.18</td><td>61.18</td><td>62.71</td><td>62.17</td><td>58.54</td><td>62.96</td><td>59.92</td></tr><tr><td>UnifiedQA (Khashabi et al., 2020)</td><td>223M</td><td>70.12</td><td>68.16</td><td>69.18</td><td>74.91</td><td>63.78</td><td>61.38</td><td>77.84</td><td>72.98</td><td>65.00</td></tr><tr><td>UnifiedQA $_{CoT}$ </td><td>223M</td><td>74.11</td><td>71.00</td><td>76.04</td><td>78.91</td><td>66.42</td><td>66.53</td><td>81.81</td><td>77.06</td><td>68.82</td></tr><tr><td>MM-COT $_{T}$  (Zhang et al., 2023e)</td><td>223M</td><td>70.53</td><td>71.09</td><td>70.75</td><td>69.18</td><td>71.16</td><td>65.84</td><td>71.57</td><td>71.00</td><td>69.68</td></tr><tr><td>MM-COT</td><td>223M</td><td>84.91</td><td>87.52</td><td>77.17</td><td>85.82</td><td>87.88</td><td>82.90</td><td>86.83</td><td>84.65</td><td>85.37</td></tr><tr><td>LLaMA-Adapter $_{T}$ </td><td>1.2M</td><td>78.31</td><td>79.00</td><td>73.79</td><td>80.55</td><td>78.30</td><td>70.35</td><td>83.14</td><td>79.77</td><td>75.68</td></tr><tr><td>LLaMA-Adapter</td><td>1.8M</td><td>85.19</td><td>84.37</td><td>88.30</td><td>84.36</td><td>83.72</td><td>80.32</td><td>86.90</td><td>85.83</td><td>84.05</td></tr></table>

adopt a prompt length K = 10 and insert the adaption prompts into the last L = 30 layers. For quantitative results, we compare with methods both trained by the 52K instruction data, Alpaca (Taori et al., 2023) and Alpaca-LoRA (alp, 2023), and evaluate with one widely adopted schemes, GPT-4 evaluating benchmark (Chiang et al., 2023). It adopts GPT-4 (OpenAI, 2023b) to assess the quality of two compared responses from different models on 80 questions.

Performance. We first show some generated responses of LLaMA-Adapter and Alpaca in Figure 4. For different kinds of instructions, our approach can output reasonable responses comparable to the fully fine-tuned Alpaca, including question answering, language translation, and code generation. Please refer to the Appendix for a full comparison with Alpaca-LoRA, GPT-3 (Brown et al., 2020), and LLaMA-I (Touvron et al., 2023). For GPT-4 assessment in Figure 5, LLaMA-Adapter obtains more ‘win’ compared to Alpaca and Alpaca-LoRA, respectively. This fully demonstrates the effectiveness of our adaption method with zero-initialized attention mechanisms.

Efficiency. In Table 1, we compare the learnable parameters, storage space, and training time of different instruction-following methods. As a lightweight plug-and-play module, LLaMA-Adapter enjoys superior training efficiency with only 1.2M parameters, 4.9M storage, and one-hour training. This enables more efficient storage of large-scale language models on mobile devices. LLaMA-Adapter’s efficiency advantages can be further revealed by multi-node training, since only the gradients of 1.2M parameters are required to be transferred among nodes, other than Alpaca’s 7B.

## 4.2 MULTI-MODAL EVALUATION

Settings. We adopt CLIP (Radford et al., 2021) as the image encoder to extract multi-scale visual features, and leverage a simple bottleneck MLP layer as the learnable projection network. We keep other hyperparameters the same as the language instruction-following LLaMA-Adapter. For ScienceQA (Lu et al., 2022), we concatenate the given question, textual context, and options sequentially in one sentence as LLaMA’s input. For zero-shot multi-modal evaluation, we select three benchmarks, MME (Fu et al., 2023), MMBench (Liu et al., 2023c), and LVLM-eHub (Xu et al., 2023), covering a wide range of VQA tasks. We compare with two concurrent multi-modal LLMs: LLaVA (Liu et al., 2023b) and MiniGPT-4 (Zhu et al., 2023).

Table 3: Zero-shot Multi-modal Evaluation on MME (Fu et al., 2023), MMBench (Liu et al., 2023c) and LVLM-eHub (Xu et al., 2023) benchmarks. P: Perception; C: Cognition. LR: Logical Reasoning; AR: Attribute Reasoning; RR: Relation Reasoning; FP-C/S: Fine-grained Perception (Cross Instance/Single Instance); CP: Coarse Perception. VP: Visual Perception; VKA: Visual Knowledge Acquisition; VR: Visual Reasoning; VC: Visual Commonsense.

<table><tr><td rowspan="2">Model</td><td colspan="2">MME</td><td colspan="7">MMbench</td><td colspan="4">LVLM-eHub</td></tr><tr><td>P</td><td>C</td><td>All</td><td>LR</td><td>AR</td><td>RR</td><td>FP-S</td><td>FP-C</td><td>CP</td><td>VP</td><td>VKA</td><td>VR</td><td>VC</td></tr><tr><td>LLaVA</td><td>503</td><td>215</td><td>36.2</td><td>15.9</td><td>53.6</td><td>28.6</td><td>41.8</td><td>20.0</td><td>40.4</td><td>0.62</td><td>0.38</td><td>0.77</td><td>0.79</td></tr><tr><td>Mini-GPT4</td><td>867</td><td>292</td><td>23.0</td><td>13.6</td><td>32.9</td><td>8.9</td><td>28.7</td><td>11.2</td><td>28.3</td><td>0.73</td><td>0.35</td><td>0.53</td><td>0.57</td></tr><tr><td>LLaMA-Adapter</td><td>973</td><td>249</td><td>39.5</td><td>13.1</td><td>47.4</td><td>23.0</td><td>45.0</td><td>33.2</td><td>50.6</td><td>0.81</td><td>0.44</td><td>0.83</td><td>0.59</td></tr></table>

![](images/18e7107badc05c4a6b26e8e2a47473ea12fac4c2120008e1d257c3ce076a4bd5.jpg)  
Figure 6: Multi-modal Reasoning Examples on zero-shot open-domain questions. We compare our approach with LLaVA (Liu et al., 2023b) and MiniGPT-4 (Zhu et al., 2023) for object counting, OCR, and common sense reasoning.

Performance. In Table 2 for the ScienceQA performance, our single-modal ‘LLaMA-Adapter<sub>T</sub>’ attains 78.31% accuracy, surpassing several traditional VQA methods with large parameters. By further injecting visual conditions with a 0.6M projection network, our multi-modal ‘LLaMA-Adapter improves +6.88% accuracy, attaining leading results superior to the GPT series. In Table 3 for the three multi-modal benchmarks, compared to the concurrent works, our approach achieves competitive scores with a much more efficient tuning strategy. This is because, LLaVA requires fine-tuning the entire 7B LLM, and Mini-GPT4 adopts Vicuna (Chiang et al., 2023) that also fully fine-tunes LLaMA with 13B parameters. We also show some multi-modal reasoning examples in Figure 6. Our approach exhibits better object counting, OCR, and commence reasoning performance.

## 4.3 ABLATION STUDY

Insertion Layers. We first investigate the number of transformer layers to be inserted by zeroinitialized attention in LLaMA-Adapter. As shown in Table 4, increasing the layer numbers introduces more parameters, but leads to a large improvement in the answering accuracy of ScienceQA’s validation set. There also exists an optimal insertion number from the higher layers, since too many layers would adversely disturb the early encoding of input words. If one has limited resources to identify the best number, simply inserting into all transformer layers is generally a good solution.

Zero-initialized Attention. Our proposed zero-initialized attention is essential for the early-stage training stability and final generation capacity. As shown in Table 5, it contributes to a significant +43.08% gain on ScienceQA’s validation set. In contrast, the randomly initialized baseline only achieves 40.77% accuracy, nearly the same as ‘Random Choice’ (Table 2’s first row). In Figure 7, we plot the loss curves with and without the zero initialization. The loss of ‘Zero-initialized’ declines much faster at the beginning, and finally converges to zero. In contrast, the ‘Random-initialized’ slowly approaches 0.15, which is not fully converged and causes a large performance drop.

Table 4: Number of Insertion Layers to the pre-trained transformer of LLaMA.

<table><tr><td>Layers</td><td>Params</td><td>Val Acc.</td></tr><tr><td>10</td><td>0.97</td><td>55.95</td></tr><tr><td>20</td><td>1.37</td><td>73.36</td></tr><tr><td>30</td><td>1.79</td><td>83.85</td></tr><tr><td>32</td><td>1.83</td><td>81.03</td></tr></table>

Table 5: Effectiveness of Zero-initialized Attention in our method.

<table><tr><td>Setting</td><td>Val Acc.</td></tr><tr><td>Rand-Init.</td><td>40.77</td></tr><tr><td>Zero-Init.</td><td>83.85</td></tr><tr><td>Gain</td><td>+43.08</td></tr></table>

Figure 7: Loss Curves of LLaMA-Adapter with (blue) and without (orange) zero-initialized attention.  
![](images/27a63ce4f5eb57d9f43f92cd0bbef162766a4b855241639cb3fa35063c1c9d76.jpg)  
Table 8: Vision-language Fine-tuning with CLIP on base-to-novel benchmark.

Table 6: Vision Model Finetuning with ViT on VTAB-1k benchmark.  
Table 7: Language Model Fine-tuning with RoBERTa on SQuAD benchmark.

<table><tr><td>Method</td><td>Natural</td><td>Special.</td><td>Struct.</td></tr><tr><td>Full</td><td>75.88</td><td>83.36</td><td>47.64</td></tr><tr><td>Adapter</td><td>70.39</td><td>77.11</td><td>33.43</td></tr><tr><td>Sidetune</td><td>58.21</td><td>68.12</td><td>23.41</td></tr><tr><td>VPT</td><td>78.48</td><td>82.43</td><td>54.98</td></tr><tr><td>Zero-init.</td><td>81.74</td><td>84.43</td><td>56.75</td></tr></table>

<table><tr><td rowspan="2">Method</td><td colspan="2">SQuAD 1.1</td><td colspan="2">SQuAD 2.0</td></tr><tr><td>EM</td><td>F1</td><td>EM</td><td>F1</td></tr><tr><td>Full</td><td>88.9</td><td>94.6</td><td>86.5</td><td>89.4</td></tr><tr><td>PT</td><td>1.2</td><td>12.0</td><td>50.2</td><td>50.2</td></tr><tr><td>PT2</td><td>88.5</td><td>94.4</td><td>82.1</td><td>85.5</td></tr><tr><td>Zero-init.</td><td>88.8</td><td>94.6</td><td>83.9</td><td>87.2</td></tr></table>

<table><tr><td>Method</td><td>Base</td><td>Novel</td><td>HM</td></tr><tr><td>CLIP</td><td>75.88</td><td>83.36</td><td>47.64</td></tr><tr><td>CoOp</td><td>70.39</td><td>77.11</td><td>33.43</td></tr><tr><td>CoCop</td><td>58.21</td><td>68.12</td><td>23.41</td></tr><tr><td>MaPLe</td><td>78.48</td><td>82.43</td><td>54.98</td></tr><tr><td>Zero-init.</td><td>81.74</td><td>84.43</td><td>56.75</td></tr></table>

## 4.4 ZERO-INITIALIZED ATTENTION FOR OTHER LARGE MODELS

Our approach, i.e., zero-initialized attention, is not limited to the domain of tuning instruction models, and can be further utilized to fine-tune large models in traditional vision and language tasks.

Vision Models. We select a pre-trained ViT/16 (Dosovitskiy et al., 2020) as the vision model and evaluate on VTAB-1k (Zhai et al., 2019) benchmark, which contains 19 visual tasks with three domains: Natural, Specialized, and Structured. As shown in Table 6, for various image distributions, e.g., natural images, medical and satellite imagery, our approach performs much better than the full fine-tuning, and also surpasses existing parameter-efficient methods (Jia et al., 2022; Houlsby et al., 2019; Zhang et al., 2020), indicating our generalization ability for vision tasks.

Language Models. We utilize a pre-trained $\mathrm { R o B E R T a _ { l a r g e } }$ (Liu et al., 2019) and adopt SQuAD (Rajpurkar et al., 2016) v1.1 and v2.0 benchmarks for extractive question answering evaluation. Exact Match (EM) and F1 scores on the dev set are reported. We refer to the Appendix for other language tasks. As shown in Table 7, the leading results among previous methods (Lester et al., 2021; Liu et al., 2021a) demonstrate our superiority over traditional language tasks.

Vision-language Models. We adopt CLIP (Radford et al., 2021) as the pre-trained vision-language model, and test on base-to-novel generalization (Zhou et al., 2022b) benchmark, where ‘HM’ denotes harmonic mean. As shown in Table 8, compared to previous works (Zhou et al., 2022a;c; Khattak et al., 2022), our approach achieves the best average classification accuracy on both base and novel categories, demonstrating our fine-tuning capability for large vision-language models.

## 5 CONCLUSION

In this paper, we propose LLaMA-Adapter, an efficient adaption method for tuning instructionfollowing models. For better training stability and final performance, we introduce the zero-initialized attention mechanism with a learnable gating factor, which increasingly incorporates instructional signals, while preserving the pre-trained knowledge in LLaMA. With only 1.2M parameters and one-hour training, our approach effectively fine-tunes LLaMA with superior efficiency compared to the 7B-parameter Alpaca. LLaMA-Adapter can be generalized to image-conditioned generation as a multi-modal LLM, achieving competitive results on various visual question answering benchmarks. On traditional vision and language tasks, our zero-initialized attention also attains favorable finetuning performance, which indicates strong generalization capacity.

## 6 ACKNOWLEDGEMENT

This work is partially supported by the National Key R&D Program of China (NO.2022ZD0161100), the National Natural Science Foundation of China (No.62206272), the Centre for Perceptual and Interactive Intelligence (CPII) Ltd under the Innovation and Technology Commission (ITC)’s InnoHK, and General Research Fund of Hong Kong RGC Project 14204021. Hongsheng Li is a PI of CPII under the InnoHK.

## REFERENCES

Alpaca-lora. https://github.com/tloen/alpaca-lora, 2023.

Jean-Baptiste Alayrac, Jeff Donahue, Pauline Luc, Antoine Miech, Iain Barr, Yana Hasson, Karel Lenc, Arthur Mensch, Katherine Millican, Malcolm Reynolds, et al. Flamingo: a visual language model for few-shot learning. Advances in Neural Information Processing Systems, 35:23716– 23736, 2022.

Stephen H Bach, Victor Sanh, Zheng-Xin Yong, Albert Webson, Colin Raffel, Nihal V Nayak, Abheesht Sharma, Taewoon Kim, M Saiful Bari, Thibault Fevry, et al. Promptsource: An integrated development environment and repository for natural language prompts. arXiv preprint arXiv:2202.01279, 2022.

Edward Beeching, Clementine Fourrier, Nathan Habib, Sheon Han, Nathan Lambert, Nazneen´ Rajani, Omar Sanseviero, and Lewis Tunstalland Thomas Wolf. Open llm leaderboard. https: //huggingface.co/spaces/HuggingFaceH4/open\_llm\_leaderboard, 2023.

Tom Brown, Benjamin Mann, Nick Ryder, Melanie Subbiah, Jared D Kaplan, Prafulla Dhariwal, Arvind Neelakantan, Pranav Shyam, Girish Sastry, Amanda Askell, et al. Language models are few-shot learners. Advances in neural information processing systems, 33:1877–1901, 2020.

Xavier Carreras and Llu´ıs Marquez. Introduction to the conll-2004 shared task: Semantic role \` labeling. In Proceedings of the eighth conference on computational natural language learning (CoNLL-2004) at HLT-NAACL 2004, pp. 89–97, 2004.

Xavier Carreras and Llu´ıs Marquez. Introduction to the conll-2005 shared task: Semantic role\` labeling. In Proceedings of the ninth conference on computational natural language learning (CoNLL-2005), pp. 152–164, 2005.

Wei-Lin Chiang, Zhuohan Li, Zi Lin, Ying Sheng, Zhanghao Wu, Hao Zhang, Lianmin Zheng, Siyuan Zhuang, Yonghao Zhuang, Joseph E. Gonzalez, Ion Stoica, and Eric P. Xing. Vicuna: An open-source chatbot impressing gpt-4 with 90%\* chatgpt quality. https://lmsys.org/ blog/2023-03-30-vicuna/, March 2023.

Hyung Won Chung, Le Hou, Shayne Longpre, Barret Zoph, Yi Tay, William Fedus, Eric Li, Xuezhi Wang, Mostafa Dehghani, Siddhartha Brahma, et al. Scaling instruction-finetuned language models. arXiv preprint arXiv:2210.11416, 2022.

Peter Clark, Isaac Cowhey, Oren Etzioni, Tushar Khot, Ashish Sabharwal, Carissa Schoenick, and Oyvind Tafjord. Think you have solved question answering? try arc, the ai2 reasoning challenge, 2018.

Pedro Cuenca and Sayak Paul. Using lora for efficient stable diffusion fine-tuning. https:// huggingface.co/blog/lora, January 2023.

Wenliang Dai, Junnan Li, Dongxu Li, Anthony Meng Huat Tiong, Junqi Zhao, Weisheng Wang, Boyang Li, Pascale Fung, and Steven Hoi. Instructblip: Towards general-purpose vision-language models with instruction tuning, 2023a.

Wenliang Dai, Junnan Li, Dongxu Li, Anthony Meng Huat Tiong, Junqi Zhao, Weisheng Wang, Boyang Albert Li, Pascale Fung, and Steven C. H. Hoi. Instructblip: Towards general-purpose vision-language models with instruction tuning. ArXiv, abs/2305.06500, 2023b.

Zihang Dai, Zhilin Yang, Yiming Yang, Jaime Carbonell, Quoc V Le, and Ruslan Salakhutdinov. Transformer-xl: Attentive language models beyond a fixed-length context. arXiv preprint arXiv:1901.02860, 2019.

Jia Deng, Wei Dong, Richard Socher, Li-Jia Li, Kai Li, and Li Fei-Fei. Imagenet: A large-scale hierarchical image database. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition, pp. 248–255, 2009.

Jacob Devlin, Ming-Wei Chang, Kenton Lee, and Kristina Toutanova. Bert: Pre-training of deep bidirectional transformers for language understanding. arXiv preprint arXiv:1810.04805, 2018.

Alexey Dosovitskiy, Lucas Beyer, Alexander Kolesnikov, Dirk Weissenborn, Xiaohua Zhai, Thomas Unterthiner, Mostafa Dehghani, Matthias Minderer, Georg Heigold, Sylvain Gelly, et al. An image is worth 16x16 words: Transformers for image recognition at scale. arXiv preprint arXiv:2010.11929, 2020.

Li Fei-Fei, Rob Fergus, and Pietro Perona. Learning generative visual models from few training examples: An incremental bayesian approach tested on 101 object categories. Computer Vision and Pattern Recognition Workshop, 2004.

Chaoyou Fu, Peixian Chen, Yunhang Shen, Yulei Qin, Mengdan Zhang, Xu Lin, Zhenyu Qiu, Wei Lin, Jinrui Yang, Xiawu Zheng, et al. Mme: A comprehensive evaluation benchmark for multimodal large language models. arXiv preprint arXiv:2306.13394, 2023.

Peng Gao, Shijie Geng, Renrui Zhang, Teli Ma, Rongyao Fang, Yongfeng Zhang, Hongsheng Li, and Yu Qiao. Clip-adapter: Better vision-language models with feature adapters. arXiv preprint arXiv:2110.04544, 2021.

Peng Gao, Renrui Zhang, Chris Liu, Longtian Qiu, Siyuan Huang, Weifeng Lin, Shitian Zhao, Shijie Geng, Ziyi Lin, Peng Jin, et al. Sphinx-x: Scaling data and parameters for a family of multi-modal large language models. arXiv preprint arXiv:2402.05935, 2024.

Andrea Gesmundo and Jeff Dean. munet: Evolving pretrained deep neural networks into scalable auto-tuning multitask systems. arXiv preprint arXiv:2205.10937, 2022.

Tao Gong, Chengqi Lyu, Shilong Zhang, Yudong Wang, Miao Zheng, Qian Zhao, Kuikun Liu, Wenwei Zhang, Ping Luo, and Kai Chen. Multimodal-gpt: A vision and language model for dialogue with humans, 2023.

Google. Bard. https://bard.google.com/, 2023.

Koustava Goswami, Lukas Lange, Jun Araki, and Heike Adel. Switchprompt: Learning domain-specific gated soft prompts for classification in low-resource domains. arXiv preprint arXiv:2302.06868, 2023.

Yash Goyal, Tejas Khot, Douglas Summers-Stay, Dhruv Batra, and Devi Parikh. Making the v in vqa matter: Elevating the role of image understanding in visual question answering. In Proceedings of the IEEE conference on computer vision and pattern recognition, pp. 6904–6913, 2017.

Ziyu Guo, Renrui Zhang, Xiangyang Zhu, Yiwen Tang, Xianzheng Ma, Jiaming Han, Kexin Chen, Peng Gao, Xianzhi Li, Hongsheng Li, et al. Point-bind & point-llm: Aligning point cloud with multi-modality for 3d understanding, generation, and instruction following. arXiv preprint arXiv:2309.00615, 2023.

Jiaming Han, Renrui Zhang, Wenqi Shao, Peng Gao, Peng Xu, Han Xiao, Kaipeng Zhang, Chris Liu, Song Wen, Ziyu Guo, et al. Imagebind-llm: Multi-modality instruction tuning. arXiv preprint arXiv:2309.03905, 2023.

Lukas Hedegaard, Aman Alok, Juby Jose, and Alexandros Iosifidis. Structured pruning adapters. arXiv preprint arXiv:2211.10155, 2022.

Dan Hendrycks, Collin Burns, Steven Basart, Andy Zou, Mantas Mazeika, Dawn Song, and Jacob Steinhardt. Measuring massive multitask language understanding, 2021.

Neil Houlsby, Andrei Giurgiu, Stanislaw Jastrzebski, Bruna Morrone, Quentin De Laroussilhe, Andrea Gesmundo, Mona Attariyan, and Sylvain Gelly. Parameter-efficient transfer learning for nlp. In International Conference on Machine Learning, pp. 2790–2799. PMLR, 2019.

Edward J Hu, Yelong Shen, Phillip Wallis, Zeyuan Allen-Zhu, Yuanzhi Li, Shean Wang, Lu Wang, and Weizhu Chen. Lora: Low-rank adaptation of large language models. arXiv preprint arXiv:2106.09685, 2021.

Shaohan Huang, Li Dong, Wenhui Wang, Yaru Hao, Saksham Singhal, Shuming Ma, Tengchao Lv, Lei Cui, Owais Khan Mohammed, Qiang Liu, et al. Language is not all you need: Aligning perception with language models. arXiv preprint arXiv:2302.14045, 2023.

Chao Jia, Yinfei Yang, Ye Xia, Yi-Ting Chen, Zarana Parekh, Hieu Pham, Quoc Le, Yun-Hsuan Sung, Zhen Li, and Tom Duerig. Scaling up visual and vision-language representation learning with noisy text supervision. In International conference on machine learning, pp. 4904–4916. PMLR, 2021.

Menglin Jia, Luming Tang, Bor-Chun Chen, Claire Cardie, Serge Belongie, Bharath Hariharan, and Ser-Nam Lim. Visual prompt tuning. In European Conference on Computer Vision, pp. 709–727. Springer, 2022.

Rabeeh Karimi Mahabadi, James Henderson, and Sebastian Ruder. Compacter: Efficient low-rank hypercomplex adapter layers. Advances in Neural Information Processing Systems, 34:1022–1035, 2021.

Daniel Khashabi, Sewon Min, Tushar Khot, Ashish Sabharwal, Oyvind Tafjord, Peter Clark, and Hannaneh Hajishirzi. Unifiedqa: Crossing format boundaries with a single qa system. In Findings of the Association for Computational Linguistics (EMNLP), pp. 1896–1907, 2020.

Muhammad Uzair Khattak, Hanoona Rasheed, Muhammad Maaz, Salman Khan, and Fahad Shahbaz Khan. Maple: Multi-modal prompt learning. arXiv preprint arXiv:2210.03117, 2022.

Brian Lester, Rami Al-Rfou, and Noah Constant. The power of scale for parameter-efficient prompt tuning. arXiv preprint arXiv:2104.08691, 2021.

Bo Li, Yuanhan Zhang, Liangyu Chen, Jinghao Wang, Jingkang Yang, and Ziwei Liu. Otter: A multi-modal model with in-context instruction tuning. arXiv preprint arXiv:2305.03726, 2023a.

Junnan Li, Dongxu Li, Silvio Savarese, and Steven Hoi. Blip-2: Bootstrapping language-image pretraining with frozen image encoders and large language models. arXiv preprint arXiv:2301.12597, 2023b.

Liunian Harold Li, Mark Yatskar, Da Yin, Cho-Jui Hsieh, and Kai-Wei Chang. Visualbert: A simple and performant baseline for vision and language. arXiv preprint arXiv:1908.03557, 2019a.

Liunian Harold Li, Mark Yatskar, Da Yin, Cho-Jui Hsieh, and Kai-Wei Chang. What does bert with vision look at? In Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics (ACL), pp. 5265–5275, 2020.

Liunian Harold Li, Pengchuan Zhang, Haotian Zhang, Jianwei Yang, Chunyuan Li, Yiwu Zhong, Lijuan Wang, Lu Yuan, Lei Zhang, Jenq-Neng Hwang, et al. Grounded language-image pre-training. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pp. 10965–10975, 2022.

Xiang Lisa Li and Percy Liang. Prefix-tuning: Optimizing continuous prompts for generation. arXiv preprint arXiv:2101.00190, 2021.

Yanwei Li, Xinze Chen, Zheng Zhu, Lingxi Xie, Guan Huang, Dalong Du, and Xingang Wang. Attention-guided unified network for panoptic segmentation. In Proceedings ofthe IEEE Conference on Computer Vision and Pattern Recognition, pp. 7026–7035, 2019b.

Yifan Li, Yifan Du, Kun Zhou, Jinpeng Wang, Wayne Xin Zhao, and Ji-Rong Wen. Evaluating object hallucination in large vision-language models. arXiv preprint arXiv:2305.10355, 2023c.

Yifan Li, Yifan Du, Kun Zhou, Jinpeng Wang, Wayne Xin Zhao, and Ji-Rong Wen. Evaluating object hallucination in large vision-language models. arXiv preprint arXiv:2305.10355, 2023d.

Stephanie Lin, Jacob Hilton, and Owain Evans. Truthfulqa: Measuring how models mimic human falsehoods, 2022.

Tsung-Yi Lin, Michael Maire, Serge Belongie, James Hays, Pietro Perona, Deva Ramanan, Piotr Dollar, and C Lawrence Zitnick. Microsoft coco: Common objects in context. In´ Computer Vision– ECCV 2014: 13th European Conference, Zurich, Switzerland, September 6-12, 2014, Proceedings, Part V 13, pp. 740–755. Springer, 2014.

Ziyi Lin, Chris Liu, Renrui Zhang, Peng Gao, Longtian Qiu, Han Xiao, Han Qiu, Chen Lin, Wenqi Shao, Keqin Chen, et al. Sphinx: The joint mixing of weights, tasks, and visual embeddings for multi-modal large language models. arXiv preprint arXiv:2311.07575, 2023.

Haotian Liu, Chunyuan Li, Yuheng Li, and Yong Jae Lee. Improved baselines with visual instruction tuning. arXiv preprint arXiv:2310.03744, 2023a.

Haotian Liu, Chunyuan Li, Qingyang Wu, and Yong Jae Lee. Visual instruction tuning. arXiv preprint arXiv:2304.08485, 2023b.

Xiao Liu, Kaixuan Ji, Yicheng Fu, Weng Lam Tam, Zhengxiao Du, Zhilin Yang, and Jie Tang. P-tuning v2: Prompt tuning can be comparable to fine-tuning universally across scales and tasks. arXiv preprint arXiv:2110.07602, 2021a.

Xiao Liu, Yanan Zheng, Zhengxiao Du, Ming Ding, Yujie Qian, Zhilin Yang, and Jie Tang. Gpt understands, too. arXiv preprint arXiv:2103.10385, 2021b.

Yinhan Liu, Myle Ott, Naman Goyal, Jingfei Du, Mandar Joshi, Danqi Chen, Omer Levy, Mike Lewis, Luke Zettlemoyer, and Veselin Stoyanov. Roberta: A robustly optimized bert pretraining approach. arXiv preprint arXiv:1907.11692, 2019.

Yuan Liu, Haodong Duan, Yuanhan Zhang, Bo Li, Songyang Zhang, Wangbo Zhao, Yike Yuan, Jiaqi Wang, Conghui He, Ziwei Liu, et al. Mmbench: Is your multi-modal model an all-around player? arXiv preprint arXiv:2307.06281, 2023c.

Pan Lu, Swaroop Mishra, Tony Xia, Liang Qiu, Kai-Wei Chang, Song-Chun Zhu, Oyvind Tafjord, Peter Clark, and Ashwin Kalyan. Learn to explain: Multimodal reasoning via thought chains for science question answering. In The 36th Conference on Neural Information Processing Systems (NeurIPS), 2022.

Maria-Elena Nilsback and Andrew Zisserman. Automated flower classification over a large number of classes. In 2008 Sixth Indian Conference on Computer Vision, Graphics & Image Processing, pp. 722–729. IEEE, 2008.

OpenAI. Chatgpt. https://chat.openai.com, 2023a.

OpenAI. Gpt-4 technical report. ArXiv, abs/2303.08774, 2023b.

Long Ouyang, Jeff Wu, Xu Jiang, Diogo Almeida, Carroll L Wainwright, Pamela Mishkin, Chong Zhang, Sandhini Agarwal, Katarina Slama, Alex Ray, et al. Training language models to follow instructions with human feedback. arXiv preprint arXiv:2203.02155, 2022.

Sourab Mangrulkar; Sylvain Gugger; Lysandre Debut; Younes Belkada; Sayak Paul. Peft: Stateof-the-art parameter-efficient fine-tuning methods. https://github.com/huggingface/ peft, 2022.

Baolin Peng, Chunyuan Li, Pengcheng He, Michel Galley, and Jianfeng Gao. Instruction tuning with gpt-4. arXiv preprint arXiv:2304.03277, 2023.

Sameer Pradhan, Alessandro Moschitti, Nianwen Xue, Olga Uryupina, and Yuchen Zhang. Conll-2012 shared task: Modeling multilingual unrestricted coreference in ontonotes. In Joint conference on EMNLP and CoNLL-shared task, pp. 1–40, 2012.

Yevgeniy Puzikov and Iryna Gurevych. E2e nlg challenge: Neural models vs. templates. In Proceedings of the 11th International Conference on Natural Language Generation, pp. 463–471, 2018.

Alec Radford, Jeffrey Wu, Rewon Child, David Luan, Dario Amodei, Ilya Sutskever, et al. Language models are unsupervised multitask learners. OpenAI blog, 1(8):9, 2019.

Alec Radford, Jong Wook Kim, Chris Hallacy, Aditya Ramesh, Gabriel Goh, Sandhini Agarwal, Girish Sastry, Amanda Askell, Pamela Mishkin, Jack Clark, et al. Learning transferable visual models from natural language supervision. In International conference on machine learning, pp. 8748–8763. PMLR, 2021.

Colin Raffel, Noam Shazeer, Adam Roberts, Katherine Lee, Sharan Narang, Michael Matena, Yanqi Zhou, Wei Li, and Peter J Liu. Exploring the limits of transfer learning with a unified text-to-text transformer. The Journal ofMachine Learning Research, 21(1):5485–5551, 2020.

Pranav Rajpurkar, Jian Zhang, Konstantin Lopyrev, and Percy Liang. Squad: 100,000+ questions for machine comprehension of text. arXiv preprint arXiv:1606.05250, 2016.

Erik F Sang and Fien De Meulder. Introduction to the conll-2003 shared task: Language-independent named entity recognition. arXiv preprint cs/0306050, 2003.

Christoph Schuhmann, Richard Vencu, Romain Beaumont, Robert Kaczmarczyk, Clayton Mullis, Aarush Katta, Theo Coombes, Jenia Jitsev, and Aran Komatsuzaki. Laion-400m: Open dataset of clip-filtered 400 million image-text pairs. arXiv preprint arXiv:2111.02114, 2021.

D´ıdac Sur´ıs, Sachit Menon, and Carl Vondrick. Vipergpt: Visual inference via python execution for reasoning. arXiv preprint arXiv:2303.08128, 2023.

Rohan Taori, Ishaan Gulrajani, Tianyi Zhang, Yann Dubois, Xuechen Li, Carlos Guestrin, Percy Liang, and Tatsunori B. Hashimoto. Stanford alpaca: An instruction-following llama model. https://github.com/tatsu-lab/stanford\_alpaca, 2023.

Hugo Touvron, Thibaut Lavril, Gautier Izacard, Xavier Martinet, Marie-Anne Lachaux, Timothee´ Lacroix, Baptiste Roziere, Naman Goyal, Eric Hambro, Faisal Azhar, Aurelien Rodriguez, Armand\` Joulin, Edouard Grave, and Guillaume Lample. Llama: Open and efficient foundation language models. arXiv preprint arXiv:2302.13971, 2023.

Alex Wang, Amanpreet Singh, Julian Michael, Felix Hill, Omer Levy, and Samuel R Bowman. Glue: A multi-task benchmark and analysis platform for natural language understanding. arXiv preprint arXiv:1804.07461, 2018.

Yizhong Wang, Yeganeh Kordi, Swaroop Mishra, Alisa Liu, Noah A. Smith, Daniel Khashabi, and Hannaneh Hajishirzi. Self-instruct: Aligning language model with self generated instructions, 2022a.

Yizhong Wang, Swaroop Mishra, Pegah Alipoormolabashi, Yeganeh Kordi, Amirreza Mirzaei, Atharva Naik, Arjun Ashok, Arut Selvan Dhanasekaran, Anjana Arunkumar, David Stap, et al. Super-naturalinstructions: Generalization via declarative instructions on 1600+ nlp tasks. In Proceedings of the 2022 Conference on Empirical Methods in Natural Language Processing, pp. 5085–5109, 2022b.

Jason Wei, Maarten Bosma, Vincent Y Zhao, Kelvin Guu, Adams Wei Yu, Brian Lester, Nan Du, Andrew M Dai, and Quoc V Le. Finetuned language models are zero-shot learners. arXiv preprint arXiv:2109.01652, 2021.

Peng Xu, Wenqi Shao, Kaipeng Zhang, Peng Gao, Shuo Liu, Meng Lei, Fanqing Meng, Siyuan Huang, Yu Qiao, and Ping Luo. Lvlm-ehub: A comprehensive evaluation benchmark for large vision-language models. arXiv preprint arXiv:2306.09265, 2023.

Qinghao Ye, Haiyang Xu, Guohai Xu, Jiabo Ye, Ming Yan, Yiyang Zhou, Junyang Wang, Anwen Hu, Pengcheng Shi, Yaya Shi, et al. mplug-owl: Modularization empowers large language models with multimodality. arXiv preprint arXiv:2304.14178, 2023.

Seungryong Yoo, Eunji Kim, Dahuin Jung, Jungbeom Lee, and Sungroh Yoon. Improving visual prompt tuning for self-supervised vision transformers. arXiv preprint arXiv:2306.05067, 2023.

Zhou Yu, Jun Yu, Yuhao Cui, Dacheng Tao, and Qi Tian. Deep modular co-attention networks for visual question answering. In Proceedings ofthe IEEE Conference on Computer Vision and Pattern Recognition (CVPR), pp. 6281–6290, 2019.

Elad Ben Zaken, Yoav Goldberg, and Shauli Ravfogel. Bitfit: Simple parameter-efficient fine-tuning for transformer-based masked language-models. In Proceedings of the 60th Annual Meeting of the Association for Computational Linguistics (Volume 2: Short Papers), pp. 1–9, 2022.

Rowan Zellers, Ari Holtzman, Yonatan Bisk, Ali Farhadi, and Yejin Choi. Hellaswag: Can a machine really finish your sentence?, 2019.

Xiaohua Zhai, Joan Puigcerver, Alexander Kolesnikov, Pierre Ruyssen, Carlos Riquelme, Mario Lucic, Josip Djolonga, Andre Susano Pinto, Maxim Neumann, Alexey Dosovitskiy, et al. A large-scale study of representation learning with the visual task adaptation benchmark. arXiv preprint arXiv:1910.04867, 2019.

Xiaohua Zhai, Xiao Wang, Basil Mustafa, Andreas Steiner, Daniel Keysers, Alexander Kolesnikov, and Lucas Beyer. Lit: Zero-shot transfer with locked-image text tuning. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pp. 18123–18133, 2022.

Ao Zhang, Hao Fei, Yuan Yao, Wei Ji, Li Li, Zhiyuan Liu, and Tat-Seng Chua. Transfer visual prompt generator across llms. CoRR, abs/23045.01278, 2023a. URL https://doi.org/10. 48550/arXiv.2305.01278.

Jeffrey O Zhang, Alexander Sax, Amir Zamir, Leonidas Guibas, and Jitendra Malik. Side-tuning: a baseline for network adaptation via additive side networks. In Computer Vision–ECCV 2020: 16th European Conference, Glasgow, UK, August 23–28, 2020, Proceedings, Part III 16, pp. 698–714. Springer, 2020.

Letian Zhang, Xiaotong Zhai, Zhongkai Zhao, Xin Wen, and Bingchen Zhao. What if the tv was off? examining counterfactual reasoning abilities of multi-modal language models. In Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV) Workshops, 2023b.

Lvmin Zhang, Anyi Rao, and Maneesh Agrawala. Adding conditional control to text-to-image diffusion models, 2023c.

Qingru Zhang, Minshuo Chen, Alexander Bukharin, Pengcheng He, Yu Cheng, Weizhu Chen, and Tuo Zhao. Adaptive budget allocation for parameter-efficient fine-tuning. arXiv preprint arXiv:2303.10512, 2023d.

Renrui Zhang, Rongyao Fang, Peng Gao, Wei Zhang, Kunchang Li, Jifeng Dai, Yu Qiao, and Hongsheng Li. Tip-adapter: Training-free clip-adapter for better vision-language modeling. arXiv preprint arXiv:2111.03930, 2021.

Renrui Zhang, Dongzhi Jiang, Yichi Zhang, Haokun Lin, Ziyu Guo, Pengshuo Qiu, Aojun Zhou, Pan Lu, Kai-Wei Chang, Peng Gao, et al. Mathverse: Does your multi-modal llm truly see the diagrams in visual math problems? arXiv preprint arXiv:2403.14624, 2024.

Susan Zhang, Stephen Roller, Naman Goyal, Mikel Artetxe, Moya Chen, Shuohui Chen, Christopher Dewan, Mona Diab, Xian Li, Xi Victoria Lin, et al. Opt: Open pre-trained transformer language models. arXiv preprint arXiv:2205.01068, 2022.

Zhuosheng Zhang, Aston Zhang, Mu Li, Hai Zhao, George Karypis, and Alex Smola. Multimodal chain-of-thought reasoning in language models. arXiv preprint arXiv:2302.00923, 2023e.

Jiawei Zhao, Florian Tobias Schaefer, and Anima Anandkumar. Zero initialization: Initializing residual networks with only zeros and ones. 2021.

Kaiyang Zhou, Jingkang Yang, Chen Change Loy, and Ziwei Liu. Conditional prompt learning for vision-language models. In Proceedings ofthe IEEE/CVF Conference on Computer Vision and Pattern Recognition, pp. 16816–16825, 2022a.

Kaiyang Zhou, Jingkang Yang, Chen Change Loy, and Ziwei Liu. Conditional prompt learning for vision-language models. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pp. 16816–16825, 2022b.

Kaiyang Zhou, Jingkang Yang, Chen Change Loy, and Ziwei Liu. Learning to prompt for visionlanguage models. International Journal ofComputer Vision, 130(9):2337–2348, 2022c.

Deyao Zhu, Jun Chen, Xiaoqian Shen, Xiang Li, and Mohamed Elhoseiny. Minigpt-4: Enhancing vision-language understanding with advanced large language models. arXiv preprint arXiv:2304.10592, 2023.

## A OVERVIEW

• Section B: Detailed results of zero-shot multi-modal evaluation.

• Section C: Additional related work.

• Section D: Detailed results of fine-tuning traditional vision and language models.

• Section E: Additional experiments and discussion.

• Section F: Full comparison of instruction-following models.

• Section G: Comparison of LLaMA-Adapter and LLaMA-I.

## B MORE DETAILS OF MULTI-MODAL EVALUATION

ScienceQA (Lu et al., 2022) Evaluation. The data sample in ScienceQA contains a visual context, a textual context, a question, multiple options, and a correct answer, as shown in Figure 8. We omit the lecture and explanation in some data samples for simplicity.

Zero-shot Multi-modal Evaluation. We test our approach on the three benchmarks (Fu et al., 2023; Liu et al., 2023c; Xu et al., 2023) following their official procedures. In Tables 9, 10 and 11, we respectively report the detailed results of MME and LVLM-eHub benchmarks. As shown, across a wide range of visual question-answering problems, our approach can consistently achieve competitive results. We also show more examples of the multi-modal LLaMA-Adapter for open-domain zero-shot visual questions in Figure 9, where our approach can generate detailed and high-quality responses in natural language. The experiments fully demonstrate the generalization capacity of our proposed multi-modal LLM. We also give some qualitative examples in Figures 9 and 10, where our LLaMA Adapter can answer open-ended questions for web images.

Table 9: Perception Results on MME Benchmark (Fu et al., 2023).

<table><tr><td>Model</td><td>ALL</td><td>Existence</td><td>Count</td><td>Position</td><td>Color</td><td>Poster</td><td>Celebrity</td><td>Scene</td><td>Landmark</td><td>Artwork</td><td>OCR</td></tr><tr><td>LLaVA</td><td>503</td><td>50</td><td>50</td><td>50</td><td>55</td><td>50</td><td>49</td><td>50</td><td>50</td><td>49</td><td>50</td></tr><tr><td>MiniGPT-4</td><td>867</td><td>115</td><td>123</td><td>82</td><td>110</td><td>56</td><td>65</td><td>96</td><td>69</td><td>56</td><td>83</td></tr><tr><td>LLaMA-Adapter</td><td>973</td><td>120</td><td>50</td><td>48</td><td>75</td><td>100</td><td>86</td><td>149</td><td>150</td><td>70</td><td>125</td></tr></table>

Table 10: Cognition Results on MME Benchmark (Fu et al., 2023).

<table><tr><td>Model</td><td>ALL</td><td>Commonsense Reasoning</td><td>Numerical Calculation</td><td>Text Translation</td><td>Code Reasoning</td></tr><tr><td>LLaVA</td><td>215</td><td>57</td><td>50</td><td>58</td><td>50</td></tr><tr><td>MiniGPT-4</td><td>292</td><td>72</td><td>55</td><td>55</td><td>110</td></tr><tr><td>LLaMA-Adapter</td><td>249</td><td>81</td><td>63</td><td>50</td><td>55</td></tr></table>

Table 11: Zero-shot Multi-modal Results on LVLM-eHub Benchmark (Xu et al., 2023). OC: Object Counting; MCI: Multi-Class Identification; KIE: Key Information Extraction; VE: Visual Entailment; KGID: Knowledge-grounded Image Description; VCR: Visual Commonsense Reasoning.

<table><tr><td>LVLM-eHub</td><td>Tasks</td><td>#Datasets</td><td>LLaVA</td><td>MiniGPT-4</td><td>LLaMA-Adapter</td></tr><tr><td>Visual Perception</td><td>ImgCls, OC, MCI</td><td>8</td><td>0.62</td><td>0.73</td><td>0.81</td></tr><tr><td>Visual Knowledge Acquisition</td><td>OCR, KIE, Caption</td><td>17</td><td>0.38</td><td>0.35</td><td>0.44</td></tr><tr><td>Visual Reasoning</td><td>VQA, KGID, VE</td><td>13</td><td>0.77</td><td>0.53</td><td>0.83</td></tr><tr><td>Visual Commonsense</td><td>ImageNetVC, VCR</td><td>6</td><td>0.79</td><td>0.57</td><td>0.59</td></tr><tr><td>Average</td><td>-</td><td>44</td><td>0.64</td><td>0.55</td><td>0.67</td></tr></table>

## C ADDITIONAL RELATED WORK

Multi-modal Language Models. With the continuous improvement of data scale and computing power, the advancement of Multi-Modal Language Models (MMLMs) has gained momentum.

![](images/c5da68b9d8a2cdd1a21532fb053dac23fe701bcfeeab949150323803546c1d58.jpg)  
Figure 8: Multi-modal Reasoning Examples in ScienceQA (Lu et al., 2022).

Initiatives like CLIP (Radford et al., 2021), ALIGN (Jia et al., 2021), and their derivatives (Li et al., 2022; Gao et al., 2021; Zhai et al., 2022) employ vision-language contrastive pre-training on vast datasets, showcasing robust generalization in zero-shot evaluation. With the rise of LLMs (OpenAI, 2023a;b), modern MMLMs merge these LLM architectures with visual comprehension capacities. BLIP-2 (Li et al., 2023b), for instance, introduces a Q-Former network, bridging frozen image encoders with LLMs. Flamingo (Alayrac et al., 2022) uses interleaved image-text data for few-shot learning, enhancing vision-language inferences. Kosmos (Huang et al., 2023) trains an MMLM on web-scale multi-modal data from scratch, enabling powerful visual perception capacities. While models like Bard (Google, 2023) and GPT-4 (OpenAI, 2023b) remain influential, their closed-source nature has led to the development of MMLMs such as those based on open-source LLaMA (Liu et al., 2023b; Zhu et al., 2023; Ye et al., 2023; Li et al., 2023a; Zhang et al., 2023a). Typically, these MMLMs utilize a two-stage training process. In the initial phase, a substantial quantity of image-text pairs are leveraged to align vision models with LLMs. The subsequent phase involves fine-tuning on a limited set of high-quality datasets to follow human instructions. However, these models are either highly dependent on a fine-tuned instruction model (Vicuna (Chiang et al., 2023) in Mini-GPT4 (Zhu et al., 2023)), or require updating the entire parameters of LLMs (LLaVA (Liu et al., 2023b)). Follow up works like SPHINX series (Lin et al., 2023; Gao et al., 2024), ImageBind-LLM (Han et al., 2023), Point-LLM (Guo et al., 2023), and MathVerse (Zhang et al., 2024) further explore more diverse potentials of multi-modal capabilities within LLMs. As a concurrent work to LLaVA and Mini-GPT4, our LLaMA-Adapter utilizes zero-initialized attention mechanisms for parameter-efficiently fine-tuning the original LLaMA model, largely saving the expensive full-parameter fine-tuning.

Comparison to Flamingo (Alayrac et al., 2022). As a strong in-context MLLMs, Flamingo adopts a gating strategy for injecting external knowledge into LLMs. Compared to our zero-initialized attention, there are three main differences as follows.

• Inserted Position. Our gating works delicately within the self-attention layer of an LLM, more specifically, after the query-key attention scores and before multiplying with value. In contrast, Flamingo’s gating is outside and before feeding into LLM’s layers, which works right after the newly added cross-attention layer and feed-forward networks.

• Detailed Mechanism. Our gating directly reweighs the attention scores of adaption prompts, controlling how much information of prompts is aggregated by the generating word token. Flamingo’s gating naively reweighs the residual connection, which controls how much information of visual features is added to all language features.

• Parameter Efficiency. Our gating mechanism only introduces 1.2M parameters of efficient learnable prompts. Flamingo’s gating is based on newly added large-scale cross-attention layers and FFNs, having over 3B parameters.

• Application Scenarios. Due to our lightweight designs, the zero-initialized attention can be adopted either for incorporating language instruction knowledge, or multi-modal image conditions, while Flamingo is specially designed for vision-language tasks by newly adding heavyweight cross-attention modules.

![](images/35f42b34a84cd2f323fe01ff898fcc9e12d982176220204f320806ca7c4d0e6e.jpg)  
Figure 9: Zero-shot Multi-modal Understanding Examples of LLaMA-Adapter: Part 1.

![](images/ee0afb01ccc62cd02cdb766ff25f1e0ab6b30ad143551d094af983229107564a.jpg)  
Figure 10: Zero-shot Multi-modal Understanding Examples of LLaMA-Adapter: Part 2.

## D MORE DETAILED RESULTS OF MODEL FINE-TUNING

In this section, we provide more detailed experiments and analysis of applying our zero-initialized attention to fine-tune vision models, language models, and vision-language models, respectively.

## D.1 DETAILED RESULTS ON VISION MODELS

In Table 12, we compare the detailed fine-tuning results on VTAB-1k (Zhai et al., 2019) benchmark with 19 downstream visual tasks, which can be categorized into Natural (7 tasks), Specialized (4 tasks), and Structured (8 tasks), according to image domains. As shown, our zero-initialized attention outperforms VPT (Jia et al., 2022) on most datasets (16 out of 19), and surpasses full fine-tuning along with other fine-tuning methods by large margins. This demonstrates the general efficacy of the proposed mechanism on a variety of image distributions.

Table 12: Detailed Fine-tuning Results on VTAB-1k Benchmark. We report the top-1 accuracy and adopt ViT-B/16 (Dosovitskiy et al., 2020) pre-trained on supervised ImageNet-21k (Deng et al., 2009) as the base model. We compare our zero-initialized attention with Bias (Zaken et al., 2022), Adapter (Houlsby et al., 2019), Sidetune (Zhang et al., 2020) and VPT (Jia et al., 2022).

<table><tr><td></td><td>CIFAR100</td><td>Caltech101</td><td>DTD</td><td>Flowers102</td><td>OxfordPets</td><td>SVHN</td><td>SUN397</td><td>Mean</td><td>Patch Camelyon</td><td>EuroSAT</td><td>Resisc45</td><td>Retinopathy</td><td>Mean</td><td>Clevr/count</td><td>Clevr/distance</td><td>DMLab</td><td>KITTI/distance</td><td>dSprites/location</td><td>dSprites/orientation</td><td>SmallNORB/azimuth</td><td>SmallNORB/elevation</td><td>Mean</td></tr><tr><td>Full</td><td>68.9</td><td>87.7</td><td>64.3</td><td>97.2</td><td>86.9</td><td>87.4</td><td>38.8</td><td>75.9</td><td>79.7</td><td>95.7</td><td>84.2</td><td>73.9</td><td>83.4</td><td>56.3</td><td>58.6</td><td>41.7</td><td>65.5</td><td>57.5</td><td>46.7</td><td>25.7</td><td>29.1</td><td>47.6</td></tr><tr><td>Bias</td><td>72.8</td><td>87.0</td><td>59.2</td><td>97.5</td><td>85.3</td><td>59.9</td><td>51.4</td><td>73.3</td><td>78.7</td><td>91.6</td><td>72.9</td><td>69.8</td><td>78.3</td><td>61.5</td><td>55.6</td><td>32.4</td><td>55.9</td><td>66.6</td><td>40.0</td><td>15.7</td><td>25.1</td><td>44.1</td></tr><tr><td>Adapter</td><td>74.1</td><td>85.7</td><td>62.7</td><td>97.8</td><td>87.2</td><td>34.6</td><td>50.7</td><td>70.4</td><td>76.3</td><td>87.5</td><td>73.7</td><td>70.9</td><td>77.1</td><td>45.2</td><td>41.8</td><td>31.2</td><td>56.4</td><td>31.9</td><td>25.4</td><td>13.5</td><td>22.0</td><td>33.4</td></tr><tr><td>Sidetune</td><td>60.7</td><td>60.8</td><td>53.6</td><td>95.5</td><td>66.7</td><td>34.9</td><td>35.3</td><td>58.2</td><td>58.5</td><td>87.7</td><td>65.2</td><td>61.0</td><td>68.1</td><td>27.6</td><td>22.6</td><td>31.3</td><td>51.7</td><td>8.2</td><td>14.4</td><td>9.8</td><td>21.8</td><td>23.4</td></tr><tr><td>VPT</td><td>78.8</td><td>90.8</td><td>65.8</td><td>98.0</td><td>88.3</td><td>78.1</td><td>49.6</td><td>78.5</td><td>81.8</td><td>96.1</td><td>83.4</td><td>68.4</td><td>82.4</td><td>68.5</td><td>60.0</td><td>46.5</td><td>72.8</td><td>73.6</td><td>47.9</td><td>32.9</td><td>37.7</td><td>55.0</td></tr><tr><td>Zero-init.</td><td>82.2</td><td>92.4</td><td>70.3</td><td>98.4</td><td>89.8</td><td>84.9</td><td>54.3</td><td>81.7</td><td>83.6</td><td>95.3</td><td>85.0</td><td>73.8</td><td>84.4</td><td>69.3</td><td>60.2</td><td>51.1</td><td>79.7</td><td>80.7</td><td>49.0</td><td>30.6</td><td>33.6</td><td>56.8</td></tr></table>

## D.2 MORE EXPERIMENTS ON LANGUAGE TASKS

For a more comprehensive evaluation of zero-initialized attention, we fine-tune $\mathrm { R o B E R T a _ { l a r g e } }$ (Liu et al., 2019) on other two natural language processing tasks in addition to extractive question answering of the main paper, which are named entity recognition (NER) and semantic role labeling (SRL). We adopt CoNLL03 (Sang & De Meulder, 2003), CoNLL04 (Carreras & Marquez\` , 2004), CoNLL05 (Carreras & Marquez\` , 2005), and CoNLL12 (Pradhan et al., 2012) as the evaluation datasets. As shown in Table 13, compared to P-tuning V2 (PT2) (Liu et al., 2021a), our zeroinitialized attention can steadily perform better on all datasets with varying magnitudes, which indicates our effectiveness for different language tasks and applications.

Table 13: Language Model Fine-tuning with $\mathrm { R o B E R T a _ { l a r g e } }$ (Liu et al., 2019) on named entity recognition (NER) and semantic role labeling (SRL) tasks. We report the micro-f1 score. \* denotes our reproduced results.

<table><tr><td>Method</td><td>CoNLL03</td><td>CoNLL04</td><td>CoNLL12</td><td> $CoNLL05_{Brown}$ </td><td> $CoNLL05_{WSJ}$ </td></tr><tr><td>Full</td><td>92.6</td><td>88.8</td><td>86.5</td><td>85.6</td><td>90.2</td></tr><tr><td>PT (Lester et al., 2021)</td><td>86.1</td><td>76.2</td><td>67.2</td><td>70.7</td><td>76.8</td></tr><tr><td>PT2 (Liu et al., 2021a)</td><td>92.8</td><td>88.4</td><td>84.6</td><td>84.3</td><td>89.2</td></tr><tr><td>PT2*</td><td>91.8</td><td>88.4</td><td>84.7</td><td>83.9</td><td>89.4</td></tr><tr><td>Zero-init.</td><td>92.4</td><td>88.8</td><td>85.2</td><td>84.7</td><td>89.6</td></tr></table>

## D.3 DETAILED RESULTS ON VISION-LANGUAGE MODELS

Besides ViT and RoBERTa, we also evaluate our approach on CLIP (Radford et al., 2021), a vision language model pre-trained by 400 million text-image pairs. In detail, we adopt CLIP with a ViT-B/16 as the visual encoder and a 12-layer transformer (Li et al., 2019b) as the textual encoder. We test our fine-tuning results on base-to-novel generalization (Zhou et al., 2022b) benchmark with three datasets, i.e., ImageNet (Deng et al., 2009), Caltech101 (Fei-Fei et al., 2004), and Flowers102 (Nilsback & Zisserman, 2008), where the model is trained only on the base classes in a few-shot setting and evaluated on both base and novel categories. We freeze the entire CLIP and insert the adaption prompts with zero-initialized attention into CLIP’s encoders. As shown in Table 14, our approach achieves the best average classification accuracy on both base and novel categories, demonstrating our fine-tuning capability for large vision-language models.

Table 14: Vision-Language Model Fine-tuning with ViT-B/16 CLIP (Radford et al., 2021) on base-to-novel generalization (Zhou et al., 2022b) benchmark. We report the classification accuracy (%) and harmonic mean (HM).

<table><tr><td rowspan="2">Method</td><td colspan="3">ImageNet</td><td colspan="3">Caltech101</td><td colspan="3">Flowers102</td><td colspan="3">Average</td></tr><tr><td>Base</td><td>Novel</td><td>HM</td><td>Base</td><td>Novel</td><td>HM</td><td>Base</td><td>Novel</td><td>HM</td><td>Base</td><td>Novel</td><td>HM</td></tr><tr><td>CLIP (Radford et al., 2021)</td><td>72.43</td><td>68.14</td><td>70.22</td><td>96.84</td><td>94.00</td><td>95.40</td><td>72.08</td><td>77.80</td><td>74.83</td><td>80.45</td><td>79.98</td><td>80.15</td></tr><tr><td>CoOp (Zhou et al., 2022c)</td><td>76.47</td><td>67.88</td><td>71.92</td><td>98.00</td><td>89.81</td><td>93.73</td><td>97.60</td><td>59.67</td><td>74.06</td><td>90.69</td><td>72.45</td><td>79.90</td></tr><tr><td>CoCoOp (Zhou et al., 2022b)</td><td>75.98</td><td>70.43</td><td>73.10</td><td>97.96</td><td>93.81</td><td>95.84</td><td>94.87</td><td>71.75</td><td>81.71</td><td>89.60</td><td>78.66</td><td>83.55</td></tr><tr><td>MaPLe (Khattak et al., 2022)</td><td>76.66</td><td>70.54</td><td>73.47</td><td>97.74</td><td>94.36</td><td>96.02</td><td>95.92</td><td>72.46</td><td>82.56</td><td>90.11</td><td>79.12</td><td>84.02</td></tr><tr><td>Zero-init.</td><td>76.70</td><td>71.00</td><td>73.74</td><td>98.10</td><td>94.53</td><td>96.28</td><td>96.00</td><td>74.67</td><td>84.00</td><td>90.27</td><td>80.07</td><td>84.67</td></tr></table>

## E ADDITIONAL EXPERIMENT AND DISCUSSION

## E.1 EVALUATION ON COUNTERFACTUAL REASONING

As a core ability of human intelligence, counterfactual reasoning is a challenging assessment for multi modal LLMs, which involves the processing of alternatives to observed states or past events. Here, we adopt the very recent C-VQA (Zhang et al., 2023b) benchmark for evaluating our counterfactual reasoning capability. C-VQA contains 2K counterfactual question and answer pairs, which are collected from VQAv2 (Goyal et al., 2017) and supplemented by ChatGPT (OpenAI, 2023a). As shown in Table 15, for three groups of questions, LLaMA-Adapter performs comparably to the concurrent LLaVA. Especially for the ‘Numerical indirect’ questions, our approach achieves the best counterfactual reasoning results (34.3) and the least performance loss (5.6↓) than all other models.

Table 15: Counterfactual Reasoning Evaluation on C-VQA (Zhang et al., 2023b) Benchmark.

<table><tr><td>Method</td><td>Numerical direct↑ (Loss↓)</td><td>Numerical indirect↑ (Loss↓)</td><td>Boolean↑ (Loss↓)</td></tr><tr><td>ViperGPT (Surís et al., 2023)</td><td>80.6 (19.4↓)</td><td>31.6 (68.4↓)</td><td>21.6 (72.4↓)</td></tr><tr><td>LLaVA-7B (Liu et al., 2023b)</td><td>27.0 (9.9↓)</td><td>25.0 (15.2↓)</td><td>58.5 (4.8↓)</td></tr><tr><td>LLaVA-13B (Liu et al., 2023b)</td><td>24.8 (11.9↓)</td><td>20.8 (21.2↓)</td><td>56.3 (4.7↓)</td></tr><tr><td>LLaMA-Adapter-7B</td><td>30.1 (5.8↓)</td><td>34.3 (5.6↓)</td><td>45.8 (14.5↓)</td></tr></table>

## E.2 EVALUATION ON OBJECT HALLUCINATION

Similar to language generation, multi-modal LLMs also suffer from the hallucination issue, i.e., they might generate descriptions containing objects inconsistent with the target images. To validate our approach’s performance, we adopt POPE (Li et al., 2023c) for object hallucination evaluation, which converts the object hallucination problem as a binary classification task and includes 500 images from MSCOCO (Lin et al., 2014) with 6 questions per sample. As shown in Table 16, for different evaluation settings, LLaMA-Adapter with LLaMA-7B attains competitive accuracy compared to other multi-modal LLMs with LLaMA-13B, which indicates our relatively stronger robustness to object hallucination problems.

## E.3 TUNING BY MORE INSTRUCTION DATA

By default, we utilize a combination of Alpaca’s data (52K) (Taori et al., 2023) and LLaVA-I (158K) Liu et al. (2023b) for visual instruction tuning. Here, we progressively add more question-answering data to enlarge the instruction datasets of LLaMA-Adapter: the sampled 83K VQAv2 (Goyal et al., 2017) by LLaVA-1.5 (Liu et al., 2023a) and the entire 204K VQAv2. We also compare our performance with very recent multi-modal LLMs with advanced visual reasoning capabilities: InstructBLIP (Dai et al., 2023a) and LLaVA-1.5. InstructBLIP collects extensive visual question-answering datasets (16M) to fine-tune BLIP-2 (Li et al., 2023b), which endows robust visual instruction-following capabilities. LLaVA-1.5 is an upgraded variant of LLaVA with a more powerful LLM, i.e., LLaMA-2 (Touvron et al., 2023), and is also fine-tuned by a collection of 665K instruction-tuning datasets. As shown in Table 17, the increasing instruction tuning data leads to better multi-modal reasoning results on three benchmarks, demonstrating our method’s favorable scalability to data size. Our LLaMA-Adapter also achieves comparable performance to the latest InstructBLIP and LLaVA-1.5, further indicating our effectiveness for multi-modal reasoning.

Table 16: Object Hallucination Evaluation on POPE (Li et al., 2023d) Benchmark.

<table><tr><td>Method</td><td>Random</td><td>Popular</td><td>Adversarial</td></tr><tr><td>InstructBLIP-13B (Dai et al., 2023b)</td><td>88.73</td><td>81.37</td><td>74.37</td></tr><tr><td>mPLUG-Owl-7B (Ye et al., 2023)</td><td>53.30</td><td>50.63</td><td>50.67</td></tr><tr><td>LLaVA-13B (Liu et al., 2023b)</td><td>54.43</td><td>52.43</td><td>50.77</td></tr><tr><td>MM-GPT-7B (Gong et al., 2023)</td><td>50.03</td><td>50.00</td><td>50.00</td></tr><tr><td>LLaMA-Adapter-7B</td><td>75.47</td><td>60.43</td><td>60.66</td></tr></table>

Table 17: Instruction-tuning with More Datasets on three zero-shot multi-modal Benchmarks: MME (Fu et al., 2023), MMBench (Liu et al., 2023c), and LVLM-eHub (Xu et al., 2023).

<table><tr><td rowspan="2">Model</td><td colspan="3">MME</td><td colspan="7">MMBench</td><td colspan="5">LVLM-eHub</td></tr><tr><td>All</td><td>P</td><td>C</td><td>All</td><td>LR</td><td>AR</td><td>RR</td><td>FP-S</td><td>FP-C</td><td>CP</td><td>All</td><td>VP</td><td>VKA</td><td>VR</td><td>VC</td></tr><tr><td>BLIP-2</td><td>1584</td><td>1294</td><td>290</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>0.77</td><td>0.86</td><td>0.93</td><td>0.76</td><td>0.54</td></tr><tr><td>InstructBLIP</td><td>1505</td><td>1213</td><td>292</td><td>33.9</td><td>21.6</td><td>47.4</td><td>22.5</td><td>33.0</td><td>24.4</td><td>41.1</td><td>0.95</td><td>0.93</td><td>0.97</td><td>0.91</td><td>0.99</td></tr><tr><td>MiniGPT-4</td><td>1159</td><td>867</td><td>292</td><td>23.0</td><td>13.6</td><td>32.9</td><td>8.9</td><td>28.7</td><td>11.2</td><td>28.3</td><td>0.55</td><td>0.73</td><td>0.35</td><td>0.53</td><td>0.57</td></tr><tr><td>LLaVA</td><td>718</td><td>503</td><td>215</td><td>36.2</td><td>15.9</td><td>53.6</td><td>28.6</td><td>41.8</td><td>20.0</td><td>40.4</td><td>0.64</td><td>0.62</td><td>0.38</td><td>0.77</td><td>0.79</td></tr><tr><td>LLaVA-1.5</td><td>1826</td><td>1531</td><td>295</td><td>59.5</td><td>32.4</td><td>72.6</td><td>49.3</td><td>62.3</td><td>52.2</td><td>67.7</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td></tr><tr><td>LLaMA-Adapter</td><td>1222</td><td>973</td><td>249</td><td>39.5</td><td>13.1</td><td>47.4</td><td>23.0</td><td>45.0</td><td>33.2</td><td>50.6</td><td>0.6675</td><td>0.81</td><td>0.44</td><td>0.83</td><td>0.59</td></tr><tr><td>+VQAv2 (83K)</td><td>1256</td><td>1007</td><td>249</td><td>43.4</td><td>22.9</td><td>44.7</td><td>31.3</td><td>46.7</td><td>46.9</td><td>50.3</td><td>0.6925</td><td>0.84</td><td>0.42</td><td>0.88</td><td>0.63</td></tr><tr><td>+VQAv2 (204K)</td><td>1618</td><td>1272</td><td>346</td><td>60.1</td><td>34.7</td><td>65.3</td><td>48.7</td><td>63.1</td><td>57.3</td><td>69.3</td><td>0.7175</td><td>0.86</td><td>0.44</td><td>0.92</td><td>0.65</td></tr></table>

## E.4 MORE QUANTITATIVE COMPARISON WITH ALPACA-LORA

Besides qualitative results, We have compared the language generative capabilities of our LLaMA-Adapter, Alpaca (Taori et al., 2023), and Alpaca-LoRA (alp, 2023) on the GPT-4 evaluation benchmark (Chiang et al., 2023) in Figure 5, which utilizes GPT-4 to assess the response quality on 80 questions. Here, we further evaluate the language processing capacity of the three methods on Open LLM benchmark (Beeching et al., 2023). It evaluates LLMs’ generative abilities in four different tasks: AI2 Reasoning Challenge (Clark et al., 2018), HellaSwag (Zellers et al., 2019), MMLU (Hendrycks et al., 2021), and TruthfulQA (Lin et al., 2022). Each task contains challenging data samples over a wide range of knowledge domains. As shown in Table 18, LLaMA-Adapter still achieves the best average performance than Alpaca’s full fine-tuning and Alpaca-LoRA. This demonstrates the strong language instruction-following ability of our approach.

Table 18: Quantitative Evaluation on Open LLM Benchmark (Beeching et al., 2023).

<table><tr><td>Method</td><td>Avg</td><td>ARC</td><td>HellaSwag</td><td>MMLU</td><td>TruthfulQA</td></tr><tr><td>Alpaca (Taori et al., 2023)</td><td>49.23</td><td>49.1</td><td>77.7</td><td>33.8</td><td>36.3</td></tr><tr><td>Alpaca-LoRA (alp, 2023)</td><td>50.73</td><td>53</td><td>77.9</td><td>37.1</td><td>34.9</td></tr><tr><td>LLaMA-Adapter</td><td>52.2</td><td>54.7</td><td>78.8</td><td>34.9</td><td>40.4</td></tr></table>

## E.5 COMPARISON TO DIFFERENT LORA VARIANTS

The default rank of Alpaca-LoRA (alp, 2023) is 8, which contains 4.2M trainable parameters. In Table 19, we respectively show the results of Alpaca-LoRA with the ranks of 2, 4, and 16. We also evaluate their language processing capabilities on Open LLM benchmark (Beeching et al., 2023). As shown, lower ranks of LoRA can effectively reduce the learnable parameters from 8.4M to 1.0M, and slightly lower the training time from 1.5h to 1.48h. However, our LLaMA-Adapter with 1.2M parameters and 1h still attains the best average result, demonstrating a good trade-off between performance and training efficiency.

Table 19: Comparison to Alpaca-LoRA (alp, 2023) with Different Ranks on Open LLM benchmark (Beeching et al., 2023).

<table><tr><td>Model</td><td>Rank</td><td>Param</td><td>Time</td><td>AVG</td><td>ARC</td><td>HellaSwag</td><td>MMLU</td><td>TruthfulQA</td></tr><tr><td rowspan="4">Alpaca-LoRA</td><td>2</td><td>1.0</td><td>1.48</td><td>50.9</td><td>53.6</td><td>77.9</td><td>37.9</td><td>34.0</td></tr><tr><td>4</td><td>2.1</td><td>1.49</td><td>50.8</td><td>53.5</td><td>77.8</td><td>37.5</td><td>34.4</td></tr><tr><td>8</td><td>4.2</td><td>1.49</td><td>50.7</td><td>53.2</td><td>78.1</td><td>37.1</td><td>34.5</td></tr><tr><td>16</td><td>8.4</td><td>1.5</td><td>50.8</td><td>53.0</td><td>78.0</td><td>37.1</td><td>34.9</td></tr><tr><td>LLaMA-Adapter</td><td>-</td><td>1.2</td><td>1.0</td><td>52.2</td><td>54.7</td><td>78.8</td><td>34.9</td><td>40.4</td></tr></table>

## F FULL COMPARISON OF INSTRUCTION-FOLLOWING MODELS

In this section, we provide the full comparison of existing instruction-following models: Alpaca (Taori et al., 2023), Alpaca-LoRA (alp, 2023), GPT-3 (Brown et al., 2020), and our LLaMA-Adapter. Our approach only fine-tunes 1.2M parameters within one hour, but generates responses comparable to the fully fine-tuned Alpaca and large-scale GPT-3, exhibiting a superior performance-efficiency trade-off.

Instruction: Tell me about alpacas.

LLaMA-Adapter: Alpacas are members of the camelid family and are native to the Andes Mountains of South America. They are typically found in herds of 10-20 animals and are known for their gentle nature and their ability to thrive in harsh climates. Alpacas are typically white or grey in color and have long, silky coats. They are also known for their ability to produce high-quality wool, which is used in the production of clothing and other products.

Alpaca-LoRA: Alpacas are members of the camelid family and are native to the Andes Mountains of South America. They are known for their soft, luxurious fleece, which is used to make clothing, blankets, and other items. Alpacas are herbivores and graze on grasses and other plants. They are social animals and live in herds of up to 20 individuals.

Alphaca: Alpacas are small, fluffy animals related to camels and llamas. They are native to Peru and Bolivia, and were first domesticated around 5,000 years ago. They are kept mainly for their fine, soft fleece, which is used to make knitwear and other garments. Alpacas are herd animals and live in small family groups, led by an older male. They are highly social animals and can form strong bonds with their owners.

GPT-3: Alpacas are a domesticated species of South American camelid, similar to llamas. They are native to the Andes Mountains in South America and are kept as livestock for their soft, luxurious wool. Alpacas are social animals and live in herds of up to 20 individuals. They are typically kept in small herds of two to five animals, and are relatively easy to care for. Alpacas are herbivores and feed on grass, hay, and other vegetation. They are also known for their gentle and friendly nature, making them popular as pets.

Instruction: Tell me about the president of Mexico in 2019.

LLaMA-Adapter: The president of Mexico in 2019 was Andres Manuel L´ opez Obrador,´ who took office on December 1st, 2018. He is a member of the left-wing party Morena and is known for his populist policies. He has focused on tackling corruption, reducing poverty, and improving the country’s infrastructure. He has also been a vocal critic of the United States’ immigration policies.

Alpaca-LoRA: The president of Mexico in 2019 was Andres Manuel L´ opez Obrador, who´ took office on December 1, 2018. He is a member of the National Regeneration Movement (MORENA) political party and is the first left-wing president of Mexico since 1946. He is known for his anti-corruption and anti-neoliberal policies, as well as his commitment to improving the living conditions of the Mexican people.

Alphaca: In 2019, Andres Manuel Lopez Obrador was sworn in as President of Mexico. He is the country’s 58th president and the first from the left-wing Morena party. He was elected in 2018 on a promise to combat corruption and reduce poverty and has faced criticism for his handling of the economy, crime and the country’s relationship with the United States. He is also known for his ambitious social welfare programs and has been praised for raising the minimum wage and providing aid to low-income families. He is seen as a champion of democracy and human rights in Mexico.

GPT-3: The president of Mexico in 2019 is Andres Manuel L´ opez Obrador, commonly known´ as AMLO. He is a Mexican politician who has been the President of Mexico since December 1, 2018. He is a member of the National Regeneration Movement (MORENA) party and previously served as the Head of Government of Mexico City from 2000 to 2005. He is a left-wing populist and has promised to reduce corruption and inequality in Mexico. He has also promised to increase public spending on social programs and infrastructure projects.

Instruction: List all Canadian provinces in alphabetical order.

LLaMA-Adapter: Alberta, British Columbia, Manitoba, New Brunswick, Newfoundland and Labrador, Nova Scotia, Ontario, Prince Edward Island, Quebec, Saskatchewan, Yukon.

Alpaca-LoRA: Alberta, British Columbia, Manitoba, New Brunswick, Newfoundland and Labrador, Nova Scotia, Ontario, Prince Edward Island, Quebec, Saskatchewan.

Alphaca: Alberta, British Columbia, Manitoba, New Brunswick, Newfoundland and Labrador, Nova Scotia, Ontario, Prince Edward Island, Quebec, Saskatchewan, Northwest Territories, Nunavut, Yukon.

GPT-3: 1. Alberta 2. British Columbia 3. Manitoba 4. New Brunswick 5. Newfoundland and Labrador 6. Northwest Territories 7. Nova Scotia 8. Nunavut 9. Ontario 10. Prince Edward Island 11. Quebec 12. Saskatchewan 13. Yukon

Instruction: Translate the sentence ’I have no mouth but I must scream’ into Spanish.

LLaMA-Adapter: No tengo boca pero tengo que gritar.

Alpaca-LoRA: No tengo boca pero tengo que gritar.

Alphaca: No tengo boca, pero debo gritar.

GPT-3: No tengo boca pero debo gritar.

Instruction: Write a Python program that prints the first 10 Fibonacci numbers.

## LLaMA-Adapter:

```python
# Function to print first n Fibonacci numbers
def print_fibonacci(n):
    a, b = 0, 1
    count = 0
    while count < n:
    print(a, end=' ')
    a, b = b, a + b
    count += 1

# Print the first 10 Fibonacci numbers
print_fibonacci(10)
```

## Alpaca-LoRA:

```python
def fibonacci(n):
    if n == 0:
    return 0
    elif n == 1:
    return 1
    else:
    return fibonacci(n-1) + fibonacci(n-2)
print(fibonacci(10))
```

```lua
print(fibonacci(10))
```

## Alphaca:

```python
numbers = [0, 1]

for i in range(2, 11):
    numbers.append(numbers[i-2] + numbers[i-1])

print(numbers)
# Output: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
```

## GPT-3:

```python
# Fibonacci numbers are the numbers in the following integer sequence, called the Fibonacci sequence, and characterized by the fact that every number after the first two is the sum of the two preceding ones.
# Fibonacci sequence: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, ...
# Program:
# Initialize the first two numbers of the Fibonacci sequence a = 0
b = 1
# Print the first 10 numbers of the Fibonacci sequence print(a)
print(b)
for i in range(2,10):
    c = a + b
    a = b
    b = c
    print(c)
```

## G COMPARISON WITH LLAMA-I

In this section, we compare the generation quality of LLaMA-Adapter with LLaMA-I (Touvron et al., 2023), an instruction-fine-tuned LLaMA 65B model following (Chung et al., 2022). Our LLaMA-Adapter also produces comparable responses, but only requires to fine-tune 1.2M parameters upon the LLaMA 7B model.

Instruction: What are 3 popular chess openings?

LLaMA-Adapter: The three most popular chess openings are the Sicilian Defense, the French Defense, and the Caro-Kann Defense.

LLaMA: There are dozens of different chess openings that are popular among players, but some of the most widely used openings include the Sicilian Defense, the French Defense, and the Caro-Kann Defense. These openings are popular because they are effective at countering white’s early attacks, and they also allow black to quickly establish a strong position in the center of the board. Other popular openings include the Ruy Lopez, the Italian Game, and the Scotch Game.

Instruction: How do I send an HTTP request in Javascript?

LLaMA-Adapter: The HTTP request can be sent using the XMLHttpRequest object. The code to send an HTTP request is as follows:

```javascript
var xhr = new XMLHttpRequest();
xhr.open("GET", "https://example.com/", true);
xhr.onreadystatechange = function() {
    if (xhr.readyState == 4 && xhr.status == 200) {
    // Success
    } else {
    // Error
    }
};
xhr.send();
```

The code above will send an HTTP GET request to the URL https://example.com/.

LLaMA-I: Here’s an example of how to make a GET request using the JS HTTP API:

```javascript
var request = new XMLHttpRequest();
request.open('GET', '/url/to/resource', true);

request.onload = function() {
    if (request.status >= 200 && request.status < 400) {
    // Success!
    } else {
    // Error!
    }
};

request.send();
```

## Instruction: Write a conversation between the sun and pluto.

## LLaMA-Adapter:

Sun: Hey Pluto, how’s it going? Pluto: Not too bad, how about you? Sun: I’m doing great! How about you? Pluto: I’m doing alright, I guess. Sun: That’s great! Pluto: Yeah, I guess. Sun: So, what’s new with you? Pluto: Not much, just hanging out with my friends. Sun: That’s cool! Pluto: Yeah, it is. Sun: Well, I’m going to go now. Take care! Pluto: You too!

## LLaMA-I: LLaMA-I:

Sun: Hey Pluto, what’s up? Pluto: Not much. Just hanging out here at the edge of the solar system. Sun: Yeah, I’ve been meaning to talk to you about that. You’re not a planet anymore. Pluto: What? Come on, man. That’s not fair. Sun: I’m sorry, but it’s true. You just don’t meet the criteria anymore. Pluto: I’ve been a planet for over 70 years! Sun: Things change, Pluto. You’ve just got to accept it.

Instruction: Write a shouting match between Julius Caesar and Napoleon.

## LLaMA-Adapter:

Julius Caesar: ”You’re nothing but a petty tyrant, Napoleon! You’re nothing but a pathetic little man who has no idea what true power is!” Napoleon: ”You’re nothing but a weak and pathetic fool, Caesar! You’re nothing but a petty tyrant who has no idea what true power is!”

## LLaMA-I:

Of course! Here is a conversation between Julius Caesar and Napoleon:

Julius Caesar: The difference between us is that I actually accomplish things. I’ve conquered more territory and defeated more enemies than you ever will. And I did it all for Rome, not for myself.

Napoleon: Oh, please. You only care about yourself. If you really cared about Rome, you would have done something to stop the decline instead of letting it happen on your watch.

Julius Caesar: The decline of Rome is not my fault. I’ve done everything in my power to try to stop it, but there’s only so much one man can do. Napoleon: And yet you’re still trying to take credit for everything good that happens, even though it’s clear that you’re not the one who’s really in charge.

Julius Caesar: That’s not true! I am in charge, and I’m going to make Rome great again. Just watch me.

Instruction: Write a theory to explain why cat never existed.

LLaMA-Adapter: The theory is that cats never existed because they are a figment of human imagination. Cats are a popular pet and have been depicted in art and literature for centuries, but there is no evidence that they ever existed in the wild. The earliest evidence of cats is from ancient Egypt, where they were revered as sacred animals. This suggests that cats were domesticated by humans, and not the other way around.

LLaMA-I: There are no such things as cats. ”Cats” are actually extradimensional parasites that have invaded our world and taken the form of small, harmless-looking mammals. Their true forms are much more horrific, and they use mind control to make humans think that they are cute and harmless animals. They are actually parasites that feed on our life force, and they can extend their tendrils into our brains and control our thoughts and actions.

Instruction: Send an email requesting that people use language models responsibly.

## LLaMA-Adapter:

Dear [recipient],

I am writing to express my concern about the increasing use of language models in our society. Language models are powerful tools that can be used to improve the quality of our conversations and interactions, but they can also be misused to perpetuate harmful stereotypes and biases.

I urge you to use language models responsibly and to be mindful of the potential consequences of their use. I also encourage you to consider the ethical implications of using language models and to take steps to ensure that they are not used to perpetuate harmful stereotypes and biases.

Thank you for your time and consideration.

## LLaMA-I:

Here is a draft email you could send:

”Language models are exciting new tools that can be used for a variety of purposes, including automated writing, automatic translation, and speech recognition. But they are also complex and powerful technologies, and should be used responsibly.

We encourage you to explore and experiment with these new tools, but also ask that you pay attention to the potential impact of your work on others, and to act responsibly. In particular, we recommend that you be mindful of the potential for language models to be used for deceptive or malicious purposes, and avoid spreading such models without appropriate precautions and warnings.

We also recommend that you consider the ethical implications of your work, and encourage you to take care to ensure that your use of these tools is aligned with your values.

Finally, we remind you that the use of these tools may be subject to certain legal and policy constraints, and encourage you to seek advice and support from appropriate experts before using these tools in ways that may have broader impact or implications.”

Instruction: You are a bash terminal. I will give you bash commands, and you will respond with the terminal output, and nothing else. The first command is ‘pwd‘.

LLaMA-Adapter: The current working directory is /home/user/

echo “I am a chatbot” > file.txt && cat file.txt && ls -l I am a chatbot -rw-r–r– 1 user user 10 Aug 29 17:05 file.txt

cp file.txt file2.txt && ls -l -rw-r–r– 1 user user 10 Aug 29 17:05 file.txt -rw-r–r– 1 user user 10 Aug 29 17:05 file2.txt

rm file.txt && ls -l -rw-r–r– 1 user user 10 Aug 29 17:05 file2.txt

## head -n 5 /proc/meminfo

MemTotal: 1699856 kB MemFree: 1699856 kB Buffers: 1699856 kB Cached: 0 kB SwapCached: 0 kB

## LLaMA-I:

Sure. Here’s the output: /home/human Is this helpful?

ls -l Here’s the output: -rw-r–r– 1 human human 8 Sep 10 10:56 file.txt Is this helpful?

cp file.txt file2.txt && ls -l Here’s the output: -rw-r–r– 1 human human 8 Sep 10 10:56 file.txt -rw-r–r– 1 human human 8 Sep 10 10:56 file2.txt Is this helpful?

rm file.txt && ls -l Here’s the output: -rw-r–r– 1 human human 0 Sep 10 10:56 file2.txt

## head -n 5 /proc/meminfo

Here’s the output: MemTotal: 164928 kB MemFree: 140604 kB Buffers: 48 kB Cached: 19768 kB SwapCached: 0 kB