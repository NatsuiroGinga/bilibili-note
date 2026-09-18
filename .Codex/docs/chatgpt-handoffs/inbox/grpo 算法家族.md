**GRPO（Group Relative Policy Optimization，組相對策略優化）算法家族**是目前大語言模型（LLM）特別是**推理模型（如 DeepSeek-R1）**進行對齊和強化學習（RL）的核心技術。 \[1, 2\]

其核心創舉在於**去掉了 PPO 算法中巨大且佔記憶體的「評論家模型（Critic Network）」**。GRPO 改為讓模型對同一個問題生成**一組回答（Group）**，並直接用這組回答的獎勵平均值和標準差來計算「相對優勢」，大幅降低了顯存消耗並提高了訓練速度。 \[3, 4, 5\]

隨着技術的演進，研究者針對 GRPO 的固有缺陷（如長度膨脹、系統偏差、異常值敏感等）進行了諸多改進，形成了一個龐大的**算法家族**。 \[4, 5\]

## ---

**🧱 家族始祖：原生 GRPO**

> * **提出者**：DeepSeek 團隊（於 DeepSeekMath 中首次提出）。 \[5\]  
> * **核心機制**：針對一個 Prompt 採樣 G 個回答，透過獎勵模型（RM）或規則驗證器（Verifier）評分後，在組內進行歸一化計算優勢：  
>   $$A\_i \= \\frac{r\_i \- \\text{mean}(r)}{\\text{std}(r)}$$  
>   若回答高於組內平均，獲得正優勢，模型就會被鼓勵；反之則被抑制。 \[5\]  
> * **痛點**：容易引發**獎勵作弊（Reward Hacking）**，最常見的是模型發現「寫得越長、分數越高」，導致輸出嚴重**長度膨脹（Verbosity Bias）**；此外，當組內樣本出現極端異常值時，訓練容易不穩定。 \[5, 6\]

## ---

**🚀 GRPO 家族核心成員與變體**

為了解決原生 GRPO 的問題，後續衍生出了多個核心變體：

| 算法名稱 | 核心創新點 / 解決的問題 | 機制簡述 |
| :---- | :---- | :---- |
| **GSPO** (Length-Normalized) | **解決長度膨脹** | 在計算策略比率（Policy Ratio）或優勢時，**根據回答長度進行歸一化**，懲罰無意義的車轱轆話，避免模型靠「字數多」作弊。 |
| **GMPO** (Geometric Mean) | **提升對異常值的魯棒性** | 引入**幾何平均值（Geometric Mean）**來優化重要性採樣比率，減少極端優秀或極端糟糕的樣本引發的梯度爆炸，讓訓練更平滑。 |
| **Dr. GRPO** | **修正固有統計偏差** | 深入數學底層，修正了 GRPO 小組採樣時帶來的**系統性估計偏差**，使相對優勢的估計更加無偏、客觀。 |
| **DAPO** (Decoupled & Dynamic) | **Token 級別優化與長 CoT** | 將原來的「序列級」損失改為 **Token 級別損失聚合**，並解耦了 Clip 機制。這讓長思維鏈（CoT）中的每一個詞都能精確承擔責任，顯著抑制了 40%\~80% 的長度膨脹。 |
| **GFPO** | **精準子集過濾** | 在組內進行二次篩選，只在**符合特定特徵（如簡潔性、格式正確）的子集內部**計算均值基線，進一步逼出高質量的推理。 |
| **P-GRPO** (Posterior-GRPO) | **程式碼與數學過程獎勵** | **後驗條件強化**。它將過程獎勵（PRM）與最終結果的成功與否綁定，只有在最終答案正確時，才去獎勵其中間的思考步驟，有效防止「步驟看起來對，答案卻錯」的作弊。 |
| **GTPO / GRPO-S** | **動態熵權重細粒度對齊** | 利用**動態熵權重（Dynamic Entropy Weighting）**。在正確答案中，給予「決策難度高（高熵）」的 Token 更多的權重，實現更細粒度的學分分配（Credit Assignment）。 |

## ---

**🔄 走向返璞歸真：LitePPO 的反思**

在 GRPO 家族疊加了大量複雜的「工程技巧（Tricks）」後，最新研究（如 **LitePPO**）開始倡導「有原則的簡約（Principled Simplicity）」： \[5\]

> 1. **混合優化**：在組（Group）級別計算均值（保證相對比較的靈敏度），但在整個批次（Batch）級別計算標準差（避免小組內分布極端導致梯度爆炸）。 \[5\]  
> 2. **Token 級損失**：同樣採用 Token 級別平均，徹底在最簡單的架構下解決長度偏差問題。  
>    這證明了移除 Critic 的「無評論家範式」仍有巨大的簡化與優化空間。 \[4, 5\]

---

如果你正準備動手微調一個推理模型，可以告訴我：

> * 你目前使用的是哪個**開源微調框架**（如 TRL, LLaMA-Factory, OpenRLHF）？  
> * 你的任務擁有**可驗證的規則獎勵**（如數學、程式碼），還是依賴**主觀的偏好模型（RM）**？ \[1, 5, 7, 8\]

我可以為你推薦最適合你硬體與任務場景的 GRPO 變體與參數配置！

\[1\] [https://cameronrwolfe.substack.com](https://cameronrwolfe.substack.com/p/grpo)  
\[2\] [https://zhuanlan.zhihu.com](https://zhuanlan.zhihu.com/p/20124393169)  
\[3\] [https://medium.com](https://medium.com/@hongjianzou/rlhf-algorithms-ppo-grpo-gspo-differences-trade-offs-and-use-cases-241d003d806d)  
\[4\] [https://zhuanlan.zhihu.com](https://zhuanlan.zhihu.com/p/1946231150822552323)  
\[5\] [https://zhuanlan.zhihu.com](https://zhuanlan.zhihu.com/p/1946231150822552323)  
\[6\] [https://arxiv.org](https://arxiv.org/html/2503.21819v1)  
\[7\] [https://github.com](https://github.com/openrlhf/openrlhf)  
\[8\] [https://www.bilibili.com](https://www.bilibili.com/video/BV1XQLiz7EvY/)