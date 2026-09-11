# PDF 全文转换失败清单

由 `tools/pdf_to_fulltext.sh` 自动追加写入，每行为一次失败尝试
（同一文件可能因不同批次多次出现，以最新时间戳为准）。

- [2026-09-03 14:54:54] `raw/papers/grpo/2512.15347.pdf`：Thinking... 2512.15347.pdf Error: [] parsing failed, please try again later
- [2026-09-03 14:55:32] `raw/papers/grpo/2601.22478.pdf`：Thinking... 2601.22478.pdf Error: [] parsing failed, please try again later
- [2026-09-03 14:56:11] `raw/papers/grpo/2511.03527.pdf`：Thinking... 2511.03527.pdf Error: [] retry limit reached (5 attempts), please replace the file
- [2026-09-03 14:58:36] `raw/papers/pinn/pcap/2001-LeBoudec-Thiran-网络演算.pdf`：Thinking... 2001-LeBoudec-Thiran-网络演算.pdf Error: [-60006] number of pages exceeds limit (200 pages), please split the file and try again Hint: Document exceeds page limit. Use --pages to split into chunks and merge the results:   mineru-open-api extract doc.pdf --pages 1-200   -o part1.md   mineru-open-api extract doc.pdf --pages 201-400 -o part2.md
- [2026-09-03 15:04:20] `raw/papers/pinn/2501.06572.pdf`：Thinking... 2501.06572.pdf Error: upload /Users/bilibili/personal/note/.worktrees/ch4-dtep-pbc-20260819/raw/papers/pinn/2501.06572.pdf: Put "https://mineru.oss-cn-shanghai.aliyuncs.com/api-upload/extract/2026-09-03/834f14ca-eb22-43b5-85b3-b7b253dada98/4752d9c8-40fe-424c-8cba-a4f1a55b86d8.pdf?Expires=1788505457&OSSAccessKeyId=LTAI5t8fSGMgiRhQn4mpp926&Signature=nhzGq2GlgXr69fc445R9CEQyM7U%3D": write tcp 127.0.0.1:58517->127.0.0.1:7890: write: no buffer space available
- [2026-09-03 15:04:57] `raw/papers/pinn/2408.11104-ConFIG.pdf`：Thinking... 2408.11104-ConFIG.pdf Error: Post "https://mineru.net/api/v4/file-urls/batch": net/http: TLS handshake timeout
- [2026-09-03 15:05:20] `raw/papers/pinn/2024-Wu-MoLE.pdf`：Thinking... 2024-Wu-MoLE.pdf Error: download zip: Get "https://cdn-mineru.openxlab.org.cn/pdf/2026-09-03/550ec75f-6bab-4404-8197-b0712c3cca8a.zip": net/http: TLS handshake timeout
- [2026-09-03 15:55:23] `raw/papers/pinn/pcap/2001-LeBoudec-Thiran-网络演算.pdf`：Thinking... 2001-LeBoudec-Thiran-网络演算.pdf Error: [-60006] number of pages exceeds limit (200 pages), please split the file and try again Hint: Document exceeds page limit. Use --pages to split into chunks and merge the results:   mineru-open-api extract doc.pdf --pages 1-200   -o part1.md   mineru-open-api extract doc.pdf --pages 201-400 -o part2.md
- [2026-09-03 16:31:42] `raw/papers/methodology/2024-Angelopoulos-Conformal-Risk-Control.pdf`：Thinking... 2024-Angelopoulos-Conformal-Risk-Control.pdf Error: [] parsing failed, please try again later
