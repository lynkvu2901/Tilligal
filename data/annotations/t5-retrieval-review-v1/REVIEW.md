# T5 — Gói review nhãn retrieval (chưa phải gold)

Không có prediction/rank/score trong gói này. 8 dev + 4 test dự kiến, chia theo nhóm câu hỏi và Điều nguồn.
Câu hỏi do AI soạn sau khi đọc nguồn; không đại diện người dùng thật. Không xác minh luật hiện hành.

## Cách review

1. Tạo bản sao dataset.draft.json ở thư mục review riêng; giữ bản gốc.
2. Đọc câu hỏi, quote, toàn Điều dưới đây và raw_blocks trong source_context.jsonl; kiểm tra context/ngoại lệ.
3. Dò các Điều/văn bản thay thế trong toàn snapshot trước khi xác nhận relevance_complete. Các đề xuất không bảo đảm đầy đủ.
4. Nếu đủ căn cứ: sửa câu hỏi/nhãn nếu cần, điền relevant_units và evidence; đặt ANSWERABLE, ACCEPTED_HUMAN.
5. Điền reviewer_type=human, reviewer_id thật, reviewed_at ISO có múi giờ, notes và 5 cờ review sau khi thực sự kiểm tra.
6. Nếu chưa giải quyết được thiếu nguồn/bất định: EXCLUDED_HUMAN + lý do, relevant_units=[]; không ép vào nhãn đúng/sai.
7. Không xem kết quả BM25 trước khi chốt nhãn. Freeze dev trước; test vẫn chưa chạy, giữ riêng khỏi tuning.
Các trường review là xác nhận của người nhập, không phải cơ chế xác thực danh tính. Không để AI tự điền người duyệt.

## Đơn vị và giới hạn phép đo

Đơn vị relevant là document version + node Điều, không chỉ số Điều. Heading có thể tính tìm đúng vị trí, chưa đủ evidence.
Chỉ hit STRUCTURAL ngoài quoted và không nghi thiếu nguồn được map về Điều; các hit còn lại giữ slot unresolved-block.
Khử trùng theo đơn vị, không xóa slot bất định để nâng điểm; lấy tối đa 100 chunk BM25. Báo Recall@5/@10 và MRR@5/@10 có giới hạn này.
Nhãn chưa review hoặc chưa rà nguồn thay thế chặn phép đo. UNANSWERABLE/AMBIGUOUS chỉ thống kê loại trừ, chưa có abstention metric.

## Câu hỏi và quote ứng viên

### D01 — dev — Theo Bộ luật Lao động 45/2019/QH14 trong snapshot, tiền lương thử việc có mức tối thiểu như thế nào?

Quote có attachment HEURISTIC; phải kiểm tra ranh giới Điều từ raw trước khi nhận nhãn.

Unit ứng viên: `article::dv:26a26bbbaf752c261f7f591c32402a0513856c8fdb116432ca47414c66d58621::node:fe478994bf74e3f0bf5f8ca025fdf28a5af326a5f7829113958767745e833289`

Chunk: `chunk:c750d325eefc4be9e1b3b06e8dc91d433d48c771687e23083342fa53030b1ab5`; Unicode offsets [0,132).

> Tiền lương của người lao động trong thời gian thử việc do hai bên thỏa thuận nhưng ít nhất phải bằng 85% mức lương của công việc đó.

### D02 — dev — Trong Bộ luật Lao động 45/2019/QH14, thời gian thử việc tối đa cho công việc cần trình độ từ cao đẳng trở lên được quy định ở đâu?

Đọc cả đoạn mở đầu Điều và các nhóm công việc, không chỉ số ngày.

Unit ứng viên: `article::dv:26a26bbbaf752c261f7f591c32402a0513856c8fdb116432ca47414c66d58621::node:3d2a30ab10faba343796d039a7d5409268f00ff5bae2f9bfb5925760ec907ccc`

Chunk: `chunk:5a10e7fc5947cfddc700fb1d960bf9d62101c8aabf60146c87a6cbbc84c42ce3`; Unicode offsets [0,118).

> 2. Không quá 60 ngày đối với công việc có chức danh nghề nghiệp cần trình độ chuyên môn, kỹ thuật từ cao đẳng trở lên;

### D03 — dev — Bộ luật Lao động 45/2019/QH14 quy định giới hạn thời giờ làm việc bình thường theo ngày và tuần như thế nào?

Đọc cả khoản 1 và 2; câu hỏi có thể cần điều kiện cách tổ chức theo tuần.

Unit ứng viên: `article::dv:26a26bbbaf752c261f7f591c32402a0513856c8fdb116432ca47414c66d58621::node:a1cae21c5608970f7101dfc6496b12ff47e627efb6369ab49b8b906de23f0577`

Chunk: `chunk:3733815e6dfc46b44f4eb0c30bd37452ad10f831082aefb6dd5701f029c66d3b`; Unicode offsets [0,98).

> 1. Thời giờ làm việc bình thường không quá 08 giờ trong 01 ngày và không quá 48 giờ trong 01 tuần.

### D04 — dev — Trong Bộ luật Lao động 45/2019/QH14, người lao động được nghỉ hằng tuần tối thiểu bao lâu và xử lý chu kỳ lao động đặc biệt ra sao?

Giữ ngoại lệ chu kỳ lao động, không rút câu thành một con số.

Unit ứng viên: `article::dv:26a26bbbaf752c261f7f591c32402a0513856c8fdb116432ca47414c66d58621::node:48b9ce03c0fc6fb3982ed9b6a0e955d196490e18bf0e2b41daba97087a6abc46`

Chunk: `chunk:d3ab2a3c5e302abc0d105d7617c79f0504ca4d263bb50c489896952c4077b9cf`; Unicode offsets [0,252).

> 1. Mỗi tuần, người lao động được nghỉ ít nhất 24 giờ liên tục. Trong trường hợp đặc biệt do chu kỳ lao động không thể nghỉ hằng tuần thì người sử dụng lao động có trách nhiệm bảo đảm cho người lao động được nghỉ tính bình quân 01 tháng ít nhất 04 ngày.

### D05 — dev — Theo Thông tư 10/2020/TT-BLĐTBXH trong snapshot, hợp đồng ghi địa điểm làm việc thế nào khi người lao động thường xuyên làm ở nhiều nơi?

Kiểm tra thêm dẫn chiếu tới Bộ luật; không mặc định đây là relevant unit duy nhất.

Unit ứng viên: `article::dv:6ab223673b530683d59614721c546eda7cfed69802f8fd94be6a692bca905d76::node:81dd536b08ec6af5c55b3387cd2ac5c0fbabe0fa0b2c4b5692aad3ef416d8e0d`

Chunk: `chunk:13ab8758b9a4769868fa81f0879ca3cb775d44c7d9fb5cbb8c509909aa17b90a`; Unicode offsets [0,224).

> b) Địa điểm làm việc của người lao động: địa điểm, phạm vi người lao động làm công việc theo thỏa thuận; trường hợp người lao động làm việc có tính chất thường xuyên ở nhiều địa điểm khác nhau thì ghi đầy đủ các địa điểm đó.

### D06 — dev — Theo Thông tư 10/2020/TT-BLĐTBXH, thỏa thuận bảo vệ bí mật kinh doanh và bí mật công nghệ có thể gồm những nội dung gì?

Phải đọc các điểm a–e dưới khoản 2; quote mở đầu chưa đủ để trả lời.

Unit ứng viên: `article::dv:6ab223673b530683d59614721c546eda7cfed69802f8fd94be6a692bca905d76::node:070223d6235d121d15d77d0decc0ecb4a6a2b1113ca2c3c10a9f58096efc6caf`

Chunk: `chunk:9ccf57b02396dc556800bca10729ea9d875cf463c0b14d161ec152be5324cefd`; Unicode offsets [0,98).

> 2. Thỏa thuận về bảo vệ bí mật kinh doanh, bí mật công nghệ có thể gồm những nội dung chủ yếu sau:

### D07 — dev — Trong bản Nghị định 145/2020/NĐ-CP của snapshot, có đủ nội dung để xác định ai thành lập Hội đồng tiền lương quốc gia không?

Ca chẩn đoán SOURCE_TEXT_POSSIBLY_INCOMPLETE; người review quyết định ambiguous/excluded. Không tự điền câu thiếu.

Unit ứng viên: `article::dv:8ff5693adaeb5220f7a578520d915c8f8b390e8178302c3fee037f692f6c8e39::node:84c53e018fb89c2bac4c3167841b298b4ad82d4ec06ef17906ff5fff9679a500`

Chunk: `chunk:c58f798fe909bee78490c3297f8bbd731dd648805f0de8dc197ed9ea7d819649`; Unicode offsets [0,31).

> Hội đồng tiền lương quốc gia do

### D08 — dev — Trong Thông tư 10/2020/TT-BLĐTBXH, khoản phụ cấp bù đắp điều kiện lao động và sinh hoạt được mô tả ở phần nào?

Tiết b1 chưa resolve; chỉ đề xuất Điều để dò nguồn, không xác nhận địa chỉ tiết. Cần đọc cả khoản và raw.

Unit ứng viên: `article::dv:6ab223673b530683d59614721c546eda7cfed69802f8fd94be6a692bca905d76::node:81dd536b08ec6af5c55b3387cd2ac5c0fbabe0fa0b2c4b5692aad3ef416d8e0d`

Chunk: `chunk:fa3213a13a02818beb1db6e295bab61f147feddf54675f59f26942c50a5bde0a`; Unicode offsets [0,232).

> b1) Các khoản phụ cấp lương để bù đắp yếu tố về điều kiện lao động, tính chất phức tạp công việc, điều kiện sinh hoạt, mức độ thu hút lao động mà mức lương thỏa thuận trong hợp đồng lao động chưa được tính đến hoặc tính chưa đầy đủ;

### T01 — test — Trong Bộ luật Lao động 45/2019/QH14, người lao động có thể đồng thời giao kết hợp đồng với nhiều người sử dụng lao động theo điều kiện nào?

Test dự kiến, không phải held-out độc lập; chưa chạy prediction cho câu này.

Unit ứng viên: `article::dv:26a26bbbaf752c261f7f591c32402a0513856c8fdb116432ca47414c66d58621::node:c4c94a65ec157bd9f2da437aeccd2202728efe12b3d7197bb5b866949ec5616f`

Chunk: `chunk:76245d2fe9da4bb90d8b3338644dc31b9adbe3d89775fcfa4ba2c9f74a22214f`; Unicode offsets [0,152).

> 1. Người lao động có thể giao kết nhiều hợp đồng lao động với nhiều người sử dụng lao động nhưng phải bảo đảm thực hiện đầy đủ các nội dung đã giao kết.

### T02 — test — Bộ luật Lao động 45/2019/QH14 yêu cầu gì về trả lương không phân biệt giới tính cho công việc có giá trị như nhau?

Đọc Điều và kiểm tra nguồn thay thế; chưa chạy prediction cho câu này.

Unit ứng viên: `article::dv:26a26bbbaf752c261f7f591c32402a0513856c8fdb116432ca47414c66d58621::node:32b23e16f1e90e37edf3e9985d6049c6df5bcacd3923d035c0f78932b4ea2bb3`

Chunk: `chunk:1cef265dc2e84c68adffed247853e46e3c8f5bc4d2adf31ed3666e2d6646cfa0`; Unicode offsets [0,143).

> 3. Người sử dụng lao động phải bảo đảm trả lương bình đẳng, không phân biệt giới tính đối với người lao động làm công việc có giá trị như nhau.

### T03 — test — Trong Bộ luật Lao động 45/2019/QH14, người lao động theo hợp đồng không xác định thời hạn thông thường phải báo trước bao lâu khi đơn phương chấm dứt?

Phải giữ ngoại lệ ngành nghề đặc thù và các trường hợp không cần báo trước; chưa chạy prediction.

Unit ứng viên: `article::dv:26a26bbbaf752c261f7f591c32402a0513856c8fdb116432ca47414c66d58621::node:04eeb27c52883afb359f93e7c493c889ea843957ea0d8f2c40dd62ffe5a11334`

Chunk: `chunk:9784fbe95005044674c9f3f133fed2ae02fb443c33a7ad09e5b808c0868015c6`; Unicode offsets [0,79).

> a) Ít nhất 45 ngày nếu làm việc theo hợp đồng lao động không xác định thời hạn;

### T04 — test — Theo Bộ luật Lao động 45/2019/QH14, khi sử dụng bao nhiêu người lao động thì nội quy lao động phải bằng văn bản?

Test dự kiến cùng corpus, không đo tổng quát sang văn bản mới; chưa chạy prediction.

Unit ứng viên: `article::dv:26a26bbbaf752c261f7f591c32402a0513856c8fdb116432ca47414c66d58621::node:7dea50388038629762acbe8bab75519402bea8cf9d194f3a87d275a6b52b1457`

Chunk: `chunk:51b043a143f8d2569dcf8a7fc57bf27d60617c737e8310d86a2e1372c86b538a`; Unicode offsets [0,138).

> 1. Người sử dụng lao động phải ban hành nội quy lao động, nếu sử dụng từ 10 người lao động trở lên thì nội quy lao động phải bằng văn bản.

## Context theo Điều ứng viên — chưa xác nhận parent bằng chuyên gia

### 45/2019/QH14 — Điều 26

`article::dv:26a26bbbaf752c261f7f591c32402a0513856c8fdb116432ca47414c66d58621::node:fe478994bf74e3f0bf5f8ca025fdf28a5af326a5f7829113958767745e833289`

- [STRUCTURAL; no issue] Điều 26. Tiền lương thử việc

- [HEURISTIC; UNNUMBERED_TEXT_CONTEXT_HEURISTIC] Tiền lương của người lao động trong thời gian thử việc do hai bên thỏa thuận nhưng ít nhất phải bằng 85% mức lương của công việc đó.

### 45/2019/QH14 — Điều 25

`article::dv:26a26bbbaf752c261f7f591c32402a0513856c8fdb116432ca47414c66d58621::node:3d2a30ab10faba343796d039a7d5409268f00ff5bae2f9bfb5925760ec907ccc`

- [STRUCTURAL; no issue] Điều 25. Thời gian thử việc

- [HEURISTIC; UNNUMBERED_TEXT_CONTEXT_HEURISTIC] Thời gian thử việc do hai bên thỏa thuận căn cứ vào tính chất và mức độ phức tạp của công việc nhưng chỉ được thử việc một lần đối với một công việc và bảo đảm điều kiện sau đây:

- [STRUCTURAL; no issue] 1. Không quá 180 ngày đối với công việc của người quản lý doanh nghiệp theo quy định của Luật Doanh nghiệp, Luật Quản lý, sử dụng vốn nhà nước đầu tư vào sản xuất, kinh doanh tại doanh nghiệp;

- [STRUCTURAL; no issue] 2. Không quá 60 ngày đối với công việc có chức danh nghề nghiệp cần trình độ chuyên môn, kỹ thuật từ cao đẳng trở lên;

- [STRUCTURAL; no issue] 3. Không quá 30 ngày đối với công việc có chức danh nghề nghiệp cần trình độ chuyên môn, kỹ thuật trung cấp, công nhân kỹ thuật, nhân viên nghiệp vụ;

- [STRUCTURAL; no issue] 4. Không quá 06 ngày làm việc đối với công việc khác.

### 45/2019/QH14 — Điều 105

`article::dv:26a26bbbaf752c261f7f591c32402a0513856c8fdb116432ca47414c66d58621::node:a1cae21c5608970f7101dfc6496b12ff47e627efb6369ab49b8b906de23f0577`

- [STRUCTURAL; no issue] Điều 105. Thời giờ làm việc bình thường

- [STRUCTURAL; no issue] 1. Thời giờ làm việc bình thường không quá 08 giờ trong 01 ngày và không quá 48 giờ trong 01 tuần.

- [STRUCTURAL; no issue] 2. Người sử dụng lao động có quyền quy định thời giờ làm việc theo ngày hoặc tuần nhưng phải thông báo cho người lao động biết; trường hợp theo tuần thì thời giờ làm việc bình thường không quá 10 giờ trong 01 ngày và không quá 48 giờ trong 01 tuần.

- [HEURISTIC; UNNUMBERED_TEXT_CONTEXT_HEURISTIC] Nhà nước khuyến khích người sử dụng lao động thực hiện tuần làm việc 40 giờ đối với người lao động.

- [STRUCTURAL; no issue] 3. Người sử dụng lao động có trách nhiệm bảo đảm giới hạn thời gian làm việc tiếp xúc với yếu tố nguy hiểm, yếu tố có hại đúng theo quy chuẩn kỹ thuật quốc gia và pháp luật có liên quan.

### 45/2019/QH14 — Điều 111

`article::dv:26a26bbbaf752c261f7f591c32402a0513856c8fdb116432ca47414c66d58621::node:48b9ce03c0fc6fb3982ed9b6a0e955d196490e18bf0e2b41daba97087a6abc46`

- [STRUCTURAL; no issue] Điều 111. Nghỉ hằng tuần

- [STRUCTURAL; no issue] 1. Mỗi tuần, người lao động được nghỉ ít nhất 24 giờ liên tục. Trong trường hợp đặc biệt do chu kỳ lao động không thể nghỉ hằng tuần thì người sử dụng lao động có trách nhiệm bảo đảm cho người lao động được nghỉ tính bình quân 01 tháng ít nhất 04 ngày.

- [STRUCTURAL; no issue] 2. Người sử dụng lao động có quyền quyết định sắp xếp ngày nghỉ hằng tuần vào ngày Chủ nhật hoặc ngày xác định khác trong tuần nhưng phải ghi vào nội quy lao động.

- [STRUCTURAL; no issue] 3. Nếu ngày nghỉ hằng tuần trùng với ngày nghỉ lễ, tết quy định tại khoản 1 Điều 112 của Bộ luật này thì người lao động được nghỉ bù ngày nghỉ hằng tuần vào ngày làm việc kế tiếp.

### 10/2020/TT-BLĐTBXH — Điều 3

`article::dv:6ab223673b530683d59614721c546eda7cfed69802f8fd94be6a692bca905d76::node:81dd536b08ec6af5c55b3387cd2ac5c0fbabe0fa0b2c4b5692aad3ef416d8e0d`

- [STRUCTURAL; no issue] Điều 3. Nội dung chủ yếu của hợp đồng lao động

- [HEURISTIC; UNNUMBERED_TEXT_CONTEXT_HEURISTIC] Nội dung chủ yếu phải có của hợp đồng lao động theo khoản 1 Điều 21 của Bộ luật Lao động được quy định như sau:

- [STRUCTURAL; no issue] 1. Thông tin về tên, địa chỉ của người sử dụng lao động và họ tên, chức danh của người giao kết hợp đồng lao động bên phía người sử dụng lao động được quy định như sau:

- [STRUCTURAL; no issue] a) Tên của người sử dụng lao động: đối với doanh nghiệp, cơ quan, tổ chức, hợp tác xã, liên hiệp hợp tác xã thì lấy theo tên của doanh nghiệp, cơ quan, tổ chức, hợp tác xã, liên hiệp hợp tác xã ghi trong giấy chứng nhận đăng ký doanh nghiệp, hợp tác xã, liên hiệp hợp tác xã hoặc giấy chứng nhận đăng ký đầu tư hoặc văn bản chấp thuận chủ trương đầu tư hoặc quyết định thành lập cơ quan, tổ chức; đối với tổ hợp tác thì lấy theo tên tổ hợp tác ghi trong hợp đồng hợp tác; đối với hộ gia đình, cá nhân thì lấy theo họ tên của người đại diện hộ gia đình, cá nhân ghi trong Căn cước công dân hoặc Chứng minh nhân dân hoặc hộ chiếu được cấp;

- [STRUCTURAL; no issue] b) Địa chỉ của người sử dụng lao động: đối với doanh nghiệp, cơ quan, tổ chức, hợp tác xã, liên hiệp hợp tác xã thì lấy theo địa chỉ ghi trong giấy chứng nhận đăng ký doanh nghiệp, hợp tác xã, liên hiệp hợp tác xã hoặc giấy chứng nhận đăng ký đầu tư hoặc văn bản chấp thuận chủ trương đầu tư hoặc quyết định thành lập cơ quan, tổ chức; đối với tổ hợp tác thì lấy theo địa chỉ trong hợp đồng hợp tác; đối với hộ gia đình, cá nhân thì lấy theo địa chỉ nơi cư trú của hộ gia đình, cá nhân đó; số điện thoại, địa chỉ thư điện tử (nếu có);

- [STRUCTURAL; no issue] c) Họ tên, chức danh của người giao kết hợp đồng lao động bên phía người sử dụng lao động: ghi theo họ tên, chức danh của người có thẩm quyền giao kết hợp đồng lao động theo quy định tại khoản 3 Điều 18 của Bộ luật Lao động.

- [STRUCTURAL; no issue] 2. Thông tin về họ tên, ngày tháng năm sinh, giới tính, nơi cư trú, số thẻ Căn cước công dân hoặc Chứng minh nhân dân hoặc hộ chiếu của người giao kết hợp đồng lao động bên phía người lao động và một số thông tin khác, gồm:

- [STRUCTURAL; no issue] a) Họ tên, ngày tháng năm sinh, giới tính, địa chỉ nơi cư trú, số điện thoại, địa chỉ thư điện tử (nếu có), số thẻ Căn cước công dân hoặc Chứng minh nhân dân hoặc hộ chiếu do cơ quan có thẩm quyền cấp của người giao kết hợp đồng lao động bên phía người lao động theo quy định tại khoản 4 Điều 18 của Bộ luật Lao động;

- [STRUCTURAL; no issue] b) Số giấy phép lao động hoặc văn bản xác nhận không thuộc diện cấp giấy phép lao động do cơ quan có thẩm quyền cấp đối với người lao động là người nước ngoài;

- [STRUCTURAL; no issue] c) Họ tên, địa chỉ nơi cư trú, số thẻ Căn cước công dân hoặc Chứng minh nhân dân hoặc hộ chiếu, số điện thoại, địa chỉ thư điện tử (nếu có) của người đại diện theo pháp luật của người chưa đủ 15 tuổi.

- [STRUCTURAL; no issue] 3. Công việc và địa điểm làm việc được quy định như sau:

- [STRUCTURAL; no issue] a) Công việc: những công việc mà người lao động phải thực hiện;

- [STRUCTURAL; no issue] b) Địa điểm làm việc của người lao động: địa điểm, phạm vi người lao động làm công việc theo thỏa thuận; trường hợp người lao động làm việc có tính chất thường xuyên ở nhiều địa điểm khác nhau thì ghi đầy đủ các địa điểm đó.

- [STRUCTURAL; no issue] 4. Thời hạn của hợp đồng lao động: thời gian thực hiện hợp đồng lao động (số tháng hoặc số ngày), thời điểm bắt đầu và thời điểm kết thúc thực hiện hợp đồng lao động (đối với hợp đồng lao động xác định thời hạn); thời điểm bắt đầu thực hiện hợp đồng lao động (đối với hợp đồng lao động không xác định thời hạn).

- [STRUCTURAL; no issue] 5. Mức lương theo công việc hoặc chức danh, hình thức trả lương, kỳ hạn trả lương, phụ cấp lương và các khoản bổ sung khác được quy định như sau:

- [STRUCTURAL; no issue] a) Mức lương theo công việc hoặc chức danh: ghi mức lương tính theo thời gian của công việc hoặc chức danh theo thang lương, bảng lương do người sử dụng lao động xây dựng theo quy định tại Điều 93 của Bộ luật Lao động; đối với người lao động hưởng lương theo sản phẩm hoặc lương khoán thì ghi mức lương tính theo thời gian để xác định đơn giá sản phẩm hoặc lương khoán;

- [STRUCTURAL; no issue] b) Phụ cấp lương theo thỏa thuận của hai bên như sau:

- [REVIEW_REQUIRED; ATTACHMENT_REVIEW_REQUIRED, SUBPOINT_NOT_RESOLVED, UNNUMBERED_TEXT_CONTEXT_HEURISTIC] b1) Các khoản phụ cấp lương để bù đắp yếu tố về điều kiện lao động, tính chất phức tạp công việc, điều kiện sinh hoạt, mức độ thu hút lao động mà mức lương thỏa thuận trong hợp đồng lao động chưa được tính đến hoặc tính chưa đầy đủ;

- [REVIEW_REQUIRED; ATTACHMENT_REVIEW_REQUIRED, SUBPOINT_NOT_RESOLVED, UNNUMBERED_TEXT_CONTEXT_HEURISTIC] b2) Các khoản phụ cấp lương gắn với quá trình làm việc và kết quả thực hiện công việc của người lao động.

- [STRUCTURAL; no issue] c) Các khoản bổ sung khác theo thỏa thuận của hai bên như sau:

- [REVIEW_REQUIRED; ATTACHMENT_REVIEW_REQUIRED, SUBPOINT_NOT_RESOLVED, UNNUMBERED_TEXT_CONTEXT_HEURISTIC] c1) Các khoản bổ sung xác định được mức tiền cụ thể cùng với mức lương thỏa thuận trong hợp đồng lao động và trả thường xuyên trong mỗi kỳ trả lương;

- [REVIEW_REQUIRED; ATTACHMENT_REVIEW_REQUIRED, SUBPOINT_NOT_RESOLVED, UNNUMBERED_TEXT_CONTEXT_HEURISTIC] c2) Các khoản bổ sung không xác định được mức tiền cụ thể cùng với mức lương thỏa thuận trong hợp đồng lao động, trả thường xuyên hoặc không thường xuyên trong mỗi kỳ trả lương gắn với quá trình làm việc, kết quả thực hiện công việc của người lao động.

- [REVIEW_REQUIRED; ATTACHMENT_REVIEW_REQUIRED, UNNUMBERED_TEXT_CONTEXT_HEURISTIC] Đối với các chế độ và phúc lợi khác như thưởng theo quy định tại Điều 104 của Bộ luật Lao động, tiền thưởng sáng kiến; tiền ăn giữa ca; các khoản hỗ trợ xăng xe, điện thoại, đi lại, tiền nhà ở, tiền giữ trẻ, nuôi con nhỏ; hỗ trợ khi người lao động có thân nhân bị chết, người lao động có người thân kết hôn, sinh nhật của người lao động, trợ cấp cho người lao động gặp hoàn cảnh khó khăn khi bị tai nạn lao động, bệnh nghề nghiệp và các khoản hỗ trợ, trợ cấp khác thì ghi thành mục riêng trong hợp đồng lao động.

- [STRUCTURAL; no issue] d) Hình thức trả lương do hai bên xác định theo quy định tại Điều 96 của Bộ luật Lao động;

- [STRUCTURAL; no issue] đ) Kỳ hạn trả lương do hai bên xác định theo quy định tại Điều 97 của Bộ luật Lao động.

- [STRUCTURAL; no issue] 6. Chế độ nâng bậc, nâng lương: theo thỏa thuận của hai bên về điều kiện, thời gian, mức lương sau khi nâng bậc, nâng lương hoặc thực hiện theo thỏa ước lao động tập thể, quy định của người sử dụng lao động.

- [STRUCTURAL; no issue] 7. Thời giờ làm việc, thời giờ nghỉ ngơi: theo thỏa thuận của hai bên hoặc thỏa thuận thực hiện theo nội quy lao động, quy định của người sử dụng lao động, thỏa ước lao động tập thể và quy định của pháp luật.

- [STRUCTURAL; no issue] 8. Trang bị bảo hộ lao động cho người lao động: những loại phương tiện bảo vệ cá nhân trong lao động theo thỏa thuận của hai bên hoặc theo thỏa ước lao động tập thể hoặc theo quy định của người sử dụng lao động và quy định của pháp luật về an toàn, vệ sinh lao động.

- [STRUCTURAL; no issue] 9. Bảo hiểm xã hội, bảo hiểm y tế và bảo hiểm thất nghiệp: theo quy định của pháp luật về lao động, bảo hiểm xã hội, bảo hiểm y tế và bảo hiểm thất nghiệp.

- [STRUCTURAL; no issue] 10. Đào tạo, bồi dưỡng, nâng cao trình độ, kỹ năng nghề: quyền, nghĩa vụ và lợi ích của người sử dụng lao động và người lao động trong việc bảo đảm thời gian, kinh phí đào tạo, bồi dưỡng, nâng cao trình độ, kỹ năng nghề.

### 10/2020/TT-BLĐTBXH — Điều 4

`article::dv:6ab223673b530683d59614721c546eda7cfed69802f8fd94be6a692bca905d76::node:070223d6235d121d15d77d0decc0ecb4a6a2b1113ca2c3c10a9f58096efc6caf`

- [STRUCTURAL; no issue] Điều 4. Bảo vệ bí mật kinh doanh, bí mật công nghệ

- [STRUCTURAL; no issue] 1. Khi người lao động làm việc có liên quan trực tiếp đến bí mật kinh doanh, bí mật công nghệ theo quy định của pháp luật thì người sử dụng lao động có quyền thỏa thuận với người lao động về nội dung bảo vệ bí mật kinh doanh, bí mật công nghệ trong hợp đồng lao động hoặc bằng văn bản khác theo quy định của pháp luật.

- [STRUCTURAL; no issue] 2. Thỏa thuận về bảo vệ bí mật kinh doanh, bí mật công nghệ có thể gồm những nội dung chủ yếu sau:

- [STRUCTURAL; no issue] a) Danh mục bí mật kinh doanh, bí mật công nghệ;

- [STRUCTURAL; no issue] b) Phạm vi sử dụng bí mật kinh doanh, bí mật công nghệ;

- [STRUCTURAL; no issue] c) Thời hạn bảo vệ bí mật kinh doanh, bí mật công nghệ;

- [STRUCTURAL; no issue] d) Phương thức bảo vệ bí mật kinh doanh, bí mật công nghệ;

- [STRUCTURAL; no issue] đ) Quyền, nghĩa vụ, trách nhiệm của người lao động, người sử dụng lao động trong thời hạn bảo vệ bí mật kinh doanh, bí mật công nghệ;

- [STRUCTURAL; no issue] e) Xử lý vi phạm thỏa thuận bảo vệ bí mật kinh doanh, bí mật công nghệ.

- [STRUCTURAL; no issue] 3. Khi phát hiện người lao động vi phạm thỏa thuận bảo vệ bí mật kinh doanh, bí mật công nghệ thì người sử dụng lao động có quyền yêu cầu người lao động bồi thường theo thỏa thuận của hai bên. Trình tự, thủ tục xử lý bồi thường được thực hiện như sau:

- [STRUCTURAL; no issue] a) Trường hợp phát hiện người lao động có hành vi vi phạm trong thời hạn thực hiện hợp đồng lao động thì xử lý theo trình tự, thủ tục xử lý việc bồi thường thiệt hại quy định tại khoản 2 Điều 130 của Bộ luật Lao động;

- [STRUCTURAL; no issue] b) Trường hợp phát hiện người lao động có hành vi vi phạm sau khi chấm dứt hợp đồng lao động thì xử lý theo quy định của pháp luật dân sự và pháp luật khác có liên quan.

- [STRUCTURAL; no issue] 4. Đối với bí mật kinh doanh, bí mật công nghệ thuộc danh mục bí mật nhà nước thì thực hiện theo quy định của pháp luật về bảo vệ bí mật nhà nước.

### 145/2020/NĐ-CP — Điều 49

`article::dv:8ff5693adaeb5220f7a578520d915c8f8b390e8178302c3fee037f692f6c8e39::node:84c53e018fb89c2bac4c3167841b298b4ad82d4ec06ef17906ff5fff9679a500`

- [STRUCTURAL; no issue] Điều 49. Chức năng của Hội đồng tiền lương quốc gia

- [HEURISTIC; SOURCE_TEXT_POSSIBLY_INCOMPLETE, UNNUMBERED_TEXT_CONTEXT_HEURISTIC] Hội đồng tiền lương quốc gia do

- [STRUCTURAL; no issue] 1. Mức lương tối thiểu xác lập theo vùng (bao gồm mức lương tối thiểu theo tháng và mức lương tối thiểu theo giờ).

- [STRUCTURAL; no issue] 2. Chính sách tiền lương áp dụng đối với người lao động theo quy định của Bộ luật Lao động.

### 45/2019/QH14 — Điều 19

`article::dv:26a26bbbaf752c261f7f591c32402a0513856c8fdb116432ca47414c66d58621::node:c4c94a65ec157bd9f2da437aeccd2202728efe12b3d7197bb5b866949ec5616f`

- [STRUCTURAL; no issue] Điều 19. Giao kết nhiều hợp đồng lao động

- [STRUCTURAL; no issue] 1. Người lao động có thể giao kết nhiều hợp đồng lao động với nhiều người sử dụng lao động nhưng phải bảo đảm thực hiện đầy đủ các nội dung đã giao kết.

- [STRUCTURAL; no issue] 2. Người lao động đồng thời giao kết nhiều hợp đồng lao động với nhiều người sử dụng lao động thì việc tham gia bảo hiểm xã hội, bảo hiểm y tế, bảo hiểm thất nghiệp được thực hiện theo quy định của pháp luật về bảo hiểm xã hội, bảo hiểm y tế, bảo hiểm thất nghiệp và an toàn, vệ sinh lao động.

### 45/2019/QH14 — Điều 90

`article::dv:26a26bbbaf752c261f7f591c32402a0513856c8fdb116432ca47414c66d58621::node:32b23e16f1e90e37edf3e9985d6049c6df5bcacd3923d035c0f78932b4ea2bb3`

- [STRUCTURAL; no issue] Điều 90. Tiền lương

- [STRUCTURAL; no issue] 1. Tiền lương là số tiền mà người sử dụng lao động trả cho người lao động theo thỏa thuận để thực hiện công việc, bao gồm mức lương theo công việc hoặc chức danh, phụ cấp lương và các khoản bổ sung khác.

- [STRUCTURAL; no issue] 2. Mức lương theo công việc hoặc chức danh không được thấp hơn mức lương tối thiểu.

- [STRUCTURAL; no issue] 3. Người sử dụng lao động phải bảo đảm trả lương bình đẳng, không phân biệt giới tính đối với người lao động làm công việc có giá trị như nhau.

### 45/2019/QH14 — Điều 35

`article::dv:26a26bbbaf752c261f7f591c32402a0513856c8fdb116432ca47414c66d58621::node:04eeb27c52883afb359f93e7c493c889ea843957ea0d8f2c40dd62ffe5a11334`

- [STRUCTURAL; no issue] Điều 35. Quyền đơn phương chấm dứt hợp đồng lao động của người lao động

- [STRUCTURAL; no issue] 1. Người lao động có quyền đơn phương chấm dứt hợp đồng lao động nhưng phải báo trước cho người sử dụng lao động như sau:

- [STRUCTURAL; no issue] a) Ít nhất 45 ngày nếu làm việc theo hợp đồng lao động không xác định thời hạn;

- [STRUCTURAL; no issue] b) Ít nhất 30 ngày nếu làm việc theo hợp đồng lao động xác định thời hạn có thời hạn từ 12 tháng đến 36 tháng;

- [STRUCTURAL; no issue] c) Ít nhất 03 ngày làm việc nếu làm việc theo hợp đồng lao động xác định thời hạn có thời hạn dưới 12 tháng;

- [STRUCTURAL; no issue] d) Đối với một số ngành, nghề, công việc đặc thù thì thời hạn báo trước được thực hiện theo quy định của Chính phủ.

- [STRUCTURAL; no issue] 2. Người lao động có quyền đơn phương chấm dứt hợp đồng lao động không cần báo trước trong trường hợp sau đây:

- [STRUCTURAL; no issue] a) Không được bố trí theo đúng công việc, địa điểm làm việc hoặc không được bảo đảm điều kiện làm việc theo thỏa thuận, trừ trường hợp quy định tại Điều 29 của Bộ luật này;

- [STRUCTURAL; no issue] b) Không được trả đủ lương hoặc trả lương không đúng thời hạn, trừ trường hợp quy định tại khoản 4 Điều 97 của Bộ luật này;

- [STRUCTURAL; no issue] c) Bị người sử dụng lao động ngược đãi, đánh đập hoặc có lời nói, hành vi nhục mạ, hành vi làm ảnh hưởng đến sức khỏe, nhân phẩm, danh dự; bị cưỡng bức lao động;

- [STRUCTURAL; no issue] d) Bị quấy rối tình dục tại nơi làm việc;

- [STRUCTURAL; no issue] đ) Lao động nữ mang thai phải nghỉ việc theo quy định tại khoản 1 Điều 138 của Bộ luật này;

- [STRUCTURAL; no issue] e) Đủ tuổi nghỉ hưu theo quy định tại Điều 169 của Bộ luật này, trừ trường hợp các bên có thỏa thuận khác;

- [STRUCTURAL; no issue] g) Người sử dụng lao động cung cấp thông tin không trung thực theo quy định tại khoản 1 Điều 16 của Bộ luật này làm ảnh hưởng đến việc thực hiện hợp đồng lao động.

### 45/2019/QH14 — Điều 118

`article::dv:26a26bbbaf752c261f7f591c32402a0513856c8fdb116432ca47414c66d58621::node:7dea50388038629762acbe8bab75519402bea8cf9d194f3a87d275a6b52b1457`

- [STRUCTURAL; no issue] Điều 118. Nội quy lao động

- [STRUCTURAL; no issue] 1. Người sử dụng lao động phải ban hành nội quy lao động, nếu sử dụng từ 10 người lao động trở lên thì nội quy lao động phải bằng văn bản.

- [STRUCTURAL; no issue] 2. Nội dung nội quy lao động không được trái với pháp luật về lao động và quy định của pháp luật có liên quan. Nội quy lao động bao gồm những nội dung chủ yếu sau đây:

- [STRUCTURAL; no issue] a) Thời giờ làm việc, thời giờ nghỉ ngơi;

- [STRUCTURAL; no issue] b) Trật tự tại nơi làm việc;

- [STRUCTURAL; no issue] c) An toàn, vệ sinh lao động;

- [STRUCTURAL; no issue] d) Phòng, chống quấy rối tình dục tại nơi làm việc; trình tự, thủ tục xử lý hành vi quấy rối tình dục tại nơi làm việc;

- [STRUCTURAL; no issue] đ) Việc bảo vệ tài sản và bí mật kinh doanh, bí mật công nghệ, sở hữu trí tuệ của người sử dụng lao động;

- [STRUCTURAL; no issue] e) Trường hợp được tạm thời chuyển người lao động làm việc khác so với hợp đồng lao động;

- [STRUCTURAL; no issue] g) Các hành vi vi phạm kỷ luật lao động của người lao động và các hình thức xử lý kỷ luật lao động;

- [STRUCTURAL; no issue] h) Trách nhiệm vật chất;

- [STRUCTURAL; no issue] i) Người có thẩm quyền xử lý kỷ luật lao động.

- [STRUCTURAL; no issue] 3. Trước khi ban hành nội quy lao động hoặc sửa đổi, bổ sung nội quy lao động, người sử dụng lao động phải tham khảo ý kiến của tổ chức đại diện người lao động tại cơ sở đối với nơi có tổ chức đại diện người lao động tại cơ sở.

- [STRUCTURAL; no issue] 4. Nội quy lao động phải được thông báo đến người lao động và những nội dung chính phải được niêm yết ở những nơi cần thiết tại nơi làm việc.

- [STRUCTURAL; no issue] 5. Chính phủ quy định chi tiết Điều này.

