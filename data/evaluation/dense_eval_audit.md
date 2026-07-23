# Dense Evaluation Audit

Gold-standard audit for `data/evaluation/dense_eval.jsonl`. Each source excerpt comes from `data/retrieval/*_chunks.jsonl`.

## eval_001

- Query: Theo Bộ luật Tố tụng dân sự 2015, Bộ luật này điều chỉnh những hoạt động tố tụng dân sự nào?
- Law ID: BLTTDS_2015
- Law name: Bộ luật Tố tụng dân sự 2015
- Search law ID: BLTTDS_2015
- Gold chunk IDs: BLTTDS_2015_D1

### BLTTDS_2015_D1

- Unit type: article
- ?i?u/Kho?n/?i?m: ?i?u 1, Kho?n -, ?i?m -
- Article title: Phạm vi điều chỉnh và nhiệm vụ của Bộ luật Tố tụng dân sự

Source excerpt:

```text
Bộ luật Tố tụng dân sự quy định những nguyên tắc cơ bản trong tố tụng dân sự; trình tự, thủ tục khởi kiện để Tòa án nhân dân (sau đây gọi là Tòa án) giải quyết các vụ án về tranh chấp dân sự, hôn nhân và gia đình, kinh doanh, thương mại, lao động (sau đây gọi chung là vụ án dân sự) và trình tự, thủ tục yêu cầu để Tòa án giải quyết các việc về yêu cầu dân sự, hôn nhân và gia đình, kinh doanh, thương mại, lao động (sau đây gọi chung là việc dân sự); trình tự, thủ tục giải quyết vụ án dân sự, việc dân sự (sau đây gọi chung là vụ việc dân sự) tại Tòa án; thủ tục công nhận và cho thi hành tại Việt Nam bản án, quyết định dân sự của Tòa án nước ngoài, phán quyết của Trọng tài nước ngoài; thi hành á...
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_001`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_002

- Query: ÄÆ°Æ¡ng sá»± pháº£i lÃ m gÃ¬ vá»›i chá»©ng cá»© Ä‘á»ƒ chá»©ng minh yÃªu cáº§u cá»§a mÃ¬nh cÃ³ cÄƒn cá»©?
- Law ID: BLTTDS_2015
- Law name: Bộ luật Tố tụng dân sự 2015
- Search law ID: null
- Gold chunk IDs: BLTTDS_2015_D6_K1

### BLTTDS_2015_D6_K1

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 6, Kho?n 1, ?i?m -
- Article title: Cung cấp chứng cứ và chứng minh trong tố tụng dân sự

Source excerpt:

```text
1. Đương sự có quyền và nghĩa vụ chủ động thu thập, giao nộp chứng cứ cho Tòa án và chứng minh cho yêu cầu của mình là có căn cứ và hợp pháp.

Cơ quan, tổ chức, cá nhân khởi kiện, yêu cầu để bảo vệ quyền và lợi ích hợp pháp của người khác có quyền và nghĩa vụ thu thập, cung cấp chứng cứ, chứng minh như đương sự.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_002`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_003

- Query: Theo Bá»™ luáº­t Tá»‘ tá»¥ng dÃ¢n sá»± 2015, Viá»‡n kiá»ƒm sÃ¡t tham gia phiÃªn há»p sÆ¡ tháº©m trong nhá»¯ng viá»‡c dÃ¢n sá»± nÃ o?
- Law ID: BLTTDS_2015
- Law name: Bộ luật Tố tụng dân sự 2015
- Search law ID: BLTTDS_2015
- Gold chunk IDs: BLTTDS_2015_D21_K2

### BLTTDS_2015_D21_K2

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 21, Kho?n 2, ?i?m -
- Article title: Kiểm sát việc tuân theo pháp luật trong tố tụng dân sự

Source excerpt:

```text
2. Viện kiểm sát tham gia các phiên họp sơ thẩm đối với các việc dân sự; phiên tòa sơ thẩm đối với những vụ án do Tòa án tiến hành thu thập chứng cứ hoặc đối tượng tranh chấp là tài sản công, lợi ích công cộng, quyền sử dụng đất, nhà ở hoặc có đương sự là người chưa thành niên, người mất năng lực hành vi dân sự, người bị hạn chế năng lực hành vi dân sự, người có khó khăn trong nhận thức, làm chủ hành vi hoặc trường hợp quy định tại khoản 2 Điều 4 của Bộ luật này.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_003`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_004

- Query: Tranh cháº¥p vá» sa tháº£i vÃ  bá»“i thÆ°á»ng khi cháº¥m dá»©t há»£p Ä‘á»“ng lao Ä‘á»™ng thuá»™c tháº©m quyá»n TÃ²a Ã¡n theo cÃ¡c Ä‘iá»ƒm nÃ o?
- Law ID: BLTTDS_2015
- Law name: Bộ luật Tố tụng dân sự 2015
- Search law ID: null
- Gold chunk IDs: BLTTDS_2015_D32_K1_DA, BLTTDS_2015_D32_K1_DB

### BLTTDS_2015_D32_K1_DA

- Unit type: point
- ?i?u/Kho?n/?i?m: ?i?u 32, Kho?n 1, ?i?m a
- Article title: Những tranh chấp về lao động và tranh chấp liên quan đến lao động thuộc thẩm quyền giải quyết của Tòa án[4]

Source excerpt:

```text
a) Về xử lý kỷ luật lao động theo hình thức sa thải hoặc về trường hợp bị đơn phương chấm dứt hợp đồng lao động;
```

### BLTTDS_2015_D32_K1_DB

- Unit type: point
- ?i?u/Kho?n/?i?m: ?i?u 32, Kho?n 1, ?i?m b
- Article title: Những tranh chấp về lao động và tranh chấp liên quan đến lao động thuộc thẩm quyền giải quyết của Tòa án[4]

Source excerpt:

```text
b) Về bồi thường thiệt hại, trợ cấp khi chấm dứt hợp đồng lao động;
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_004`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_005

- Query: Theo Bá»™ luáº­t Tá»‘ tá»¥ng dÃ¢n sá»± 2015, náº¿u khÃ´ng biáº¿t nÆ¡i cÆ° trÃº cá»§a bá»‹ Ä‘Æ¡n thÃ¬ nguyÃªn Ä‘Æ¡n cÃ³ thá»ƒ yÃªu cáº§u TÃ²a Ã¡n nÆ¡i nÃ o giáº£i quyáº¿t?
- Law ID: BLTTDS_2015
- Law name: Bộ luật Tố tụng dân sự 2015
- Search law ID: BLTTDS_2015
- Gold chunk IDs: BLTTDS_2015_D40_K1_DA

### BLTTDS_2015_D40_K1_DA

- Unit type: point
- ?i?u/Kho?n/?i?m: ?i?u 40, Kho?n 1, ?i?m a
- Article title: Thẩm quyền của Tòa án theo sự lựa chọn của nguyên đơn, người yêu cầu

Source excerpt:

```text
a) Nếu không biết nơi cư trú, làm việc, trụ sở của bị đơn thì nguyên đơn có thể yêu cầu Tòa án nơi bị đơn cư trú, làm việc, có trụ sở cuối cùng hoặc nơi bị đơn có tài sản giải quyết;
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_005`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_006

- Query: NgÆ°á»i giÃ¡m Ä‘á»‹nh cÃ³ quyá»n Ä‘á»c tÃ i liá»‡u há»“ sÆ¡ vÃ  Ä‘áº·t cÃ¢u há»i vá» váº¥n Ä‘á» giÃ¡m Ä‘á»‹nh khÃ´ng?
- Law ID: BLTTDS_2015
- Law name: Bộ luật Tố tụng dân sự 2015
- Search law ID: null
- Gold chunk IDs: BLTTDS_2015_D80_K1_DA, BLTTDS_2015_D80_K1_DB

### BLTTDS_2015_D80_K1_DA

- Unit type: point
- ?i?u/Kho?n/?i?m: ?i?u 80, Kho?n 1, ?i?m a
- Article title: Quyền, nghĩa vụ của người giám định

Source excerpt:

```text
a) Được đọc tài liệu có trong hồ sơ vụ án liên quan đến đối tượng giám định; yêu cầu Tòa án cung cấp tài liệu cần thiết cho việc giám định;
```

### BLTTDS_2015_D80_K1_DB

- Unit type: point
- ?i?u/Kho?n/?i?m: ?i?u 80, Kho?n 1, ?i?m b
- Article title: Quyền, nghĩa vụ của người giám định

Source excerpt:

```text
b) Đặt câu hỏi đối với người tham gia tố tụng về những vấn đề có liên quan đến đối tượng giám định;
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_006`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_007

- Query: Theo Luật Bảo vệ môi trường 2020, Luật này quy định về hoạt động và trách nhiệm bảo vệ môi trường của những chủ thể nào?
- Law ID: LBVMT_2020
- Law name: Luật Bảo vệ môi trường 2020
- Search law ID: LBVMT_2020
- Gold chunk IDs: LBVMT_2020_D1

### LBVMT_2020_D1

- Unit type: article
- ?i?u/Kho?n/?i?m: ?i?u 1, Kho?n -, ?i?m -
- Article title: Phạm vi điều chỉnh

Source excerpt:

```text
Luật này quy định về hoạt động bảo vệ môi trường; quyền, nghĩa vụ và trách nhiệm của cơ quan, tổ chức, cộng đồng dân cư, hộ gia đình và cá nhân trong hoạt động bảo vệ môi trường.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_007`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_008

- Query: Cháº¥t tháº£i ráº¯n vÃ  cháº¥t tháº£i nguy háº¡i Ä‘Æ°á»£c Ä‘á»‹nh nghÄ©a khÃ¡c nhau nhÆ° tháº¿ nÃ o?
- Law ID: LBVMT_2020
- Law name: Luật Bảo vệ môi trường 2020
- Search law ID: null
- Gold chunk IDs: LBVMT_2020_D3_K19, LBVMT_2020_D3_K20

### LBVMT_2020_D3_K19

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 3, Kho?n 19, ?i?m -
- Article title: Giải thích từ ngữ

Source excerpt:

```text
19. Chất thải rắn là chất thải ở thể rắn hoặc bùn thải.
```

### LBVMT_2020_D3_K20

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 3, Kho?n 20, ?i?m -
- Article title: Giải thích từ ngữ

Source excerpt:

```text
20. Chất thải nguy hại là chất thải chứa yếu tố độc hại, phóng xạ, lây nhiễm, dễ cháy, dễ nổ, gây ăn mòn, gây nhiễm độc hoặc có đặc tính nguy hại khác.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_008`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_009

- Query: Theo Luáº­t Báº£o vá»‡ mÃ´i trÆ°á»ng 2020, xáº£ nÆ°á»›c tháº£i hoáº·c khÃ­ tháº£i chÆ°a xá»­ lÃ½ Ä‘áº¡t chuáº©n cÃ³ bá»‹ cáº¥m khÃ´ng?
- Law ID: LBVMT_2020
- Law name: Luật Bảo vệ môi trường 2020
- Search law ID: LBVMT_2020
- Gold chunk IDs: LBVMT_2020_D6_K2

### LBVMT_2020_D6_K2

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 6, Kho?n 2, ?i?m -
- Article title: Các hành vi bị nghiêm cấm trong hoạt động bảo vệ môi trường

Source excerpt:

```text
2. Xả nước thải, xả khí thải chưa được xử lý đạt quy chuẩn kỹ thuật môi trường ra môi trường.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_009`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_010

- Query: Dá»± Ã¡n Ä‘áº§u tÆ° hoáº·c hoáº¡t Ä‘á»™ng xáº£ tháº£i khi chÆ°a Ä‘á»§ Ä‘iá»u kiá»‡n mÃ´i trÆ°á»ng cÃ³ thuá»™c hÃ nh vi bá»‹ cáº¥m khÃ´ng?
- Law ID: LBVMT_2020
- Law name: Luật Bảo vệ môi trường 2020
- Search law ID: null
- Gold chunk IDs: LBVMT_2020_D6_K5

### LBVMT_2020_D6_K5

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 6, Kho?n 5, ?i?m -
- Article title: Các hành vi bị nghiêm cấm trong hoạt động bảo vệ môi trường

Source excerpt:

```text
5. Thực hiện dự án đầu tư hoặc xả thải khi chưa đủ điều kiện theo quy định của pháp luật về bảo vệ môi trường.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_010`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_011

- Query: Theo Luáº­t Báº£o vá»‡ mÃ´i trÆ°á»ng 2020, á»¦y ban nhÃ¢n dÃ¢n cáº¥p tá»‰nh tháº©m Ä‘á»‹nh bÃ¡o cÃ¡o Ä‘Ã¡nh giÃ¡ tÃ¡c Ä‘á»™ng mÃ´i trÆ°á»ng Ä‘á»‘i vá»›i dá»± Ã¡n nÃ o?
- Law ID: LBVMT_2020
- Law name: Luật Bảo vệ môi trường 2020
- Search law ID: LBVMT_2020
- Gold chunk IDs: LBVMT_2020_D35_K3

### LBVMT_2020_D35_K3

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 35, Kho?n 3, ?i?m -
- Article title: Thẩm quyền thẩm định báo cáo đánh giá tác động môi trường

Source excerpt:

```text
3. Ủy ban nhân dân cấp tỉnh tổ chức thẩm định báo cáo đánh giá tác động môi trường đối với dự án đầu tư trên địa bàn, trừ đối tượng quy định tại khoản 1 và khoản 2 Điều này. Bộ, cơ quan ngang Bộ có trách nhiệm phối hợp với Ủy ban nhân dân cấp tỉnh nơi có dự án phải thẩm định báo cáo đánh giá tác động môi trường đối với dự án đầu tư thuộc thẩm quyền quyết định chủ trương đầu tư, quyết định đầu tư của mình.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_011`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_012

- Query: Thá»i háº¡n cá»§a giáº¥y phÃ©p mÃ´i trÆ°á»ng cÃ³ thá»ƒ ngáº¯n hÆ¡n theo Ä‘á» nghá»‹ cá»§a chá»§ thá»ƒ nÃ o?
- Law ID: LBVMT_2020
- Law name: Luật Bảo vệ môi trường 2020
- Search law ID: null
- Gold chunk IDs: LBVMT_2020_D40_K4_DD

### LBVMT_2020_D40_K4_DD

- Unit type: point
- ?i?u/Kho?n/?i?m: ?i?u 40, Kho?n 4, ?i?m d
- Article title: Nội dung giấy phép môi trường

Source excerpt:

```text
d) Thời hạn của giấy phép môi trường có thể ngắn hơn thời hạn quy định tại các điểm a, b và c khoản này theo đề nghị của chủ dự án đầu tư, cơ sở, chủ đầu tư xây dựng và kinh doanh hạ tầng khu sản xuất, kinh doanh, dịch vụ tập trung, cụm công nghiệp (sau đây gọi chung là chủ dự án đầu tư, cơ sở).
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_012`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_013

- Query: Theo Luật Công chứng 2024, Luật này quy định những nội dung nào trong lĩnh vực công chứng?
- Law ID: LCC_2024
- Law name: Luật Công chứng 2024
- Search law ID: LCC_2024
- Gold chunk IDs: LCC_2024_D1

### LCC_2024_D1

- Unit type: article
- ?i?u/Kho?n/?i?m: ?i?u 1, Kho?n -, ?i?m -
- Article title: Phạm vi điều chỉnh

Source excerpt:

```text
Luật này quy định về công chứng viên, tổ chức hành nghề công chứng, việc hành nghề công chứng, thủ tục công chứng và quản lý nhà nước về công chứng.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_013`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_014

- Query: VÄƒn báº£n cÃ´ng chá»©ng cÃ³ hiá»‡u lá»±c ká»ƒ tá»« thá»i Ä‘iá»ƒm nÃ o?
- Law ID: LCC_2024
- Law name: Luật Công chứng 2024
- Search law ID: null
- Gold chunk IDs: LCC_2024_D6_K1

### LCC_2024_D6_K1

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 6, Kho?n 1, ?i?m -
- Article title: Hiệu lực và giá trị pháp lý của văn bản công chứng

Source excerpt:

```text
1. Văn bản công chứng có hiệu lực kể từ thời điểm được công chứng viên ký và tổ chức hành nghề công chứng đóng dấu vào văn bản; trường hợp là văn bản công chứng điện tử thì có hiệu lực theo quy định tại khoản 2 Điều 64 của Luật này.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_014`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_015

- Query: Theo Luáº­t CÃ´ng chá»©ng 2024, cÃ´ng chá»©ng viÃªn cÃ³ Ä‘Æ°á»£c cÃ´ng chá»©ng giao dá»‹ch liÃªn quan Ä‘áº¿n tÃ i sáº£n cá»§a báº£n thÃ¢n khÃ´ng?
- Law ID: LCC_2024
- Law name: Luật Công chứng 2024
- Search law ID: LCC_2024
- Gold chunk IDs: LCC_2024_D9_K1_DC

### LCC_2024_D9_K1_DC

- Unit type: point
- ?i?u/Kho?n/?i?m: ?i?u 9, Kho?n 1, ?i?m c
- Article title: Các hành vi bị nghiêm cấm

Source excerpt:

```text
c) Công chứng giao dịch có liên quan đến tài sản, lợi ích của bản thân mình hoặc của người thân thích là vợ hoặc chồng; cha đẻ, mẹ đẻ, cha nuôi, mẹ nuôi; cha đẻ, mẹ đẻ, cha nuôi, mẹ nuôi của vợ hoặc chồng; con đẻ, con nuôi, con dâu, con rể; ông nội, bà nội, ông ngoại, bà ngoại; anh ruột, chị ruột, em ruột; anh ruột, chị ruột, em ruột của vợ hoặc chồng; cháu là con của con đẻ, con nuôi;
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_015`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_016

- Query: Há»“ sÆ¡ yÃªu cáº§u cÃ´ng chá»©ng giao dá»‹ch Ä‘Ã£ soáº¡n sáºµn Ä‘Æ°á»£c tiáº¿p nháº­n hoáº·c tá»« chá»‘i nhÆ° tháº¿ nÃ o?
- Law ID: LCC_2024
- Law name: Luật Công chứng 2024
- Search law ID: null
- Gold chunk IDs: LCC_2024_D42_K2

### LCC_2024_D42_K2

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 42, Kho?n 2, ?i?m -
- Article title: Công chứng giao dịch đã được soạn thảo sẵn

Source excerpt:

```text
2. Công chứng viên kiểm tra các giấy tờ trong hồ sơ yêu cầu công chứng, nếu hồ sơ đủ, phù hợp với quy định của pháp luật thì tiếp nhận giải quyết; trường hợp từ chối tiếp nhận thì trực tiếp giải thích rõ lý do hoặc trả lời bằng văn bản có nêu rõ lý do cho người yêu cầu công chứng.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_016`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_017

- Query: Theo Luáº­t CÃ´ng chá»©ng 2024, thá»i háº¡n cÃ´ng chá»©ng Ä‘Æ°á»£c tÃ­nh tá»« khi nÃ o vÃ  tá»‘i Ä‘a bao lÃ¢u?
- Law ID: LCC_2024
- Law name: Luật Công chứng 2024
- Search law ID: LCC_2024
- Gold chunk IDs: LCC_2024_D45_K1, LCC_2024_D45_K2

### LCC_2024_D45_K1

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 45, Kho?n 1, ?i?m -
- Article title: Thời hạn công chứng

Source excerpt:

```text
1. Thời hạn công chứng được tính từ ngày công chứng viên tiếp nhận hồ sơ yêu cầu công chứng hợp lệ được ghi nhận trong sổ yêu cầu công chứng đến ngày trả kết quả công chứng. Thời gian xác minh, giám định nội dung liên quan đến giao dịch, niêm yết việc tiếp nhận công chứng văn bản phân chia di sản không tính vào thời hạn công chứng.
```

### LCC_2024_D45_K2

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 45, Kho?n 2, ?i?m -
- Article title: Thời hạn công chứng

Source excerpt:

```text
2. Thời hạn công chứng không quá 02 ngày làm việc; đối với giao dịch có nội dung phức tạp thì thời hạn công chứng có thể kéo dài hơn nhưng không quá 10 ngày làm việc. Trong trường hợp có sự kiện bất khả kháng hoặc trở ngại khách quan hoặc do nguyên nhân từ phía người yêu cầu công chứng dẫn đến không bảo đảm thời hạn theo quy định tại khoản này thì người yêu cầu công chứng có quyền thỏa thuận bằng văn bản với tổ chức hành nghề công chứng về thời hạn công chứng.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_017`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_018

- Query: CÃ´ng chá»©ng viÃªn cÃ³ cÃ¡c nghÄ©a vá»¥ nÃ o vá» nguyÃªn táº¯c hÃ nh nghá» vÃ  báº£o vá»‡ ngÆ°á»i yÃªu cáº§u cÃ´ng chá»©ng?
- Law ID: LCC_2024
- Law name: Luật Công chứng 2024
- Search law ID: null
- Gold chunk IDs: LCC_2024_D18_K2_DA, LCC_2024_D18_K2_DB

### LCC_2024_D18_K2_DA

- Unit type: point
- ?i?u/Kho?n/?i?m: ?i?u 18, Kho?n 2, ?i?m a
- Article title: Quyền và nghĩa vụ của công chứng viên

Source excerpt:

```text
a) Tuân thủ các nguyên tắc hành nghề công chứng;
```

### LCC_2024_D18_K2_DB

- Unit type: point
- ?i?u/Kho?n/?i?m: ?i?u 18, Kho?n 2, ?i?m b
- Article title: Quyền và nghĩa vụ của công chứng viên

Source excerpt:

```text
b) Tôn trọng và bảo vệ quyền, lợi ích hợp pháp của người yêu cầu công chứng;
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_018`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_019

- Query: Theo Luật Đất đai 2024, Luật này điều chỉnh những vấn đề quản lý và sử dụng đất đai nào?
- Law ID: LDD_2024
- Law name: Luật Đất đai 2024
- Search law ID: LDD_2024
- Gold chunk IDs: LDD_2024_D1

### LDD_2024_D1

- Unit type: article
- ?i?u/Kho?n/?i?m: ?i?u 1, Kho?n -, ?i?m -
- Article title: Phạm vi điều chỉnh

Source excerpt:

```text
Luật này quy định về chế độ sở hữu đất đai, quyền hạn và trách nhiệm của Nhà nước đại diện chủ sở hữu toàn dân về đất đai và thống nhất quản lý về đất đai, chế độ quản lý và sử dụng đất đai, quyền và nghĩa vụ của công dân, người sử dụng đất đối với đất đai thuộc lãnh thổ của nước Cộng hòa xã hội chủ nghĩa Việt Nam.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_019`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_020

- Query: NgÆ°á»i sá»­ dá»¥ng Ä‘áº¥t cÃ³ quyá»n Ä‘Æ°á»£c cáº¥p Giáº¥y chá»©ng nháº­n khi Ä‘Ã¡p á»©ng Ä‘iá»u kiá»‡n nÃ o?
- Law ID: LDD_2024
- Law name: Luật Đất đai 2024
- Search law ID: null
- Gold chunk IDs: LDD_2024_D26_K1

### LDD_2024_D26_K1

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 26, Kho?n 1, ?i?m -
- Article title: Quyền chung của người sử dụng đất

Source excerpt:

```text
1. Được cấp Giấy chứng nhận quyền sử dụng đất, quyền sở hữu tài sản gắn liền với đất khi có đủ điều kiện theo quy định của pháp luật về đất đai.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_020`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_021

- Query: Theo Luáº­t Äáº¥t Ä‘ai 2024, láº¥n Ä‘áº¥t, chiáº¿m Ä‘áº¥t vÃ  há»§y hoáº¡i Ä‘áº¥t cÃ³ bá»‹ nghiÃªm cáº¥m khÃ´ng?
- Law ID: LDD_2024
- Law name: Luật Đất đai 2024
- Search law ID: LDD_2024
- Gold chunk IDs: LDD_2024_D11_K1

### LDD_2024_D11_K1

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 11, Kho?n 1, ?i?m -
- Article title: Hành vi bị nghiêm cấm trong lĩnh vực đất đai

Source excerpt:

```text
1. Lấn đất, chiếm đất, hủy hoại đất.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_021`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_022

- Query: Chuyá»ƒn Ä‘áº¥t nÃ´ng nghiá»‡p sang Ä‘áº¥t phi nÃ´ng nghiá»‡p cÃ³ thuá»™c trÆ°á»ng há»£p chuyá»ƒn má»¥c Ä‘Ã­ch sá»­ dá»¥ng Ä‘áº¥t pháº£i chÃº Ã½ khÃ´ng?
- Law ID: LDD_2024
- Law name: Luật Đất đai 2024
- Search law ID: null
- Gold chunk IDs: LDD_2024_D121_K1_DB

### LDD_2024_D121_K1_DB

- Unit type: point
- ?i?u/Kho?n/?i?m: ?i?u 121, Kho?n 1, ?i?m b
- Article title: Chuyển mục đích sử dụng đất

Source excerpt:

```text
b) Chuyển đất nông nghiệp sang đất phi nông nghiệp;
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_022`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_023

- Query: Theo Luáº­t Äáº¥t Ä‘ai 2024, cÆ¡ quan nÃ o cáº¥p Giáº¥y chá»©ng nháº­n láº§n Ä‘áº§u cho ngÆ°á»i sá»­ dá»¥ng Ä‘áº¥t thuá»™c khoáº£n 3 vÃ  khoáº£n 4 Äiá»u 4?
- Law ID: LDD_2024
- Law name: Luật Đất đai 2024
- Search law ID: LDD_2024
- Gold chunk IDs: LDD_2024_D136_K1_DB

### LDD_2024_D136_K1_DB

- Unit type: point
- ?i?u/Kho?n/?i?m: ?i?u 136, Kho?n 1, ?i?m b
- Article title: Thẩm quyền cấp Giấy chứng nhận quyền sử dụng đất, quyền sở hữu tài sản gắn liền với đất

Source excerpt:

```text
b) Ủy ban nhân dân cấp huyện cấp Giấy chứng nhận quyền sử dụng đất, quyền sở hữu tài sản gắn liền với đất cho người sử dụng đất, chủ sở hữu tài sản gắn liền với đất quy định tại khoản 3 và khoản 4 Điều 4 của Luật này.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_023`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_024

- Query: NgÆ°á»i sá»­ dá»¥ng Ä‘áº¥t pháº£i sá»­ dá»¥ng Ä‘áº¥t Ä‘Ãºng má»¥c Ä‘Ã­ch vÃ  thá»±c hiá»‡n Ä‘Äƒng kÃ½, chuyá»ƒn nhÆ°á»£ng quyá»n sá»­ dá»¥ng Ä‘áº¥t nhÆ° tháº¿ nÃ o?
- Law ID: LDD_2024
- Law name: Luật Đất đai 2024
- Search law ID: null
- Gold chunk IDs: LDD_2024_D31_K1, LDD_2024_D31_K2

### LDD_2024_D31_K1

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 31, Kho?n 1, ?i?m -
- Article title: Nghĩa vụ chung của người sử dụng đất

Source excerpt:

```text
1. Sử dụng đất đúng mục đích, đúng ranh giới thửa đất, đúng quy định về sử dụng độ sâu trong lòng đất và chiều cao trên không, bảo vệ các công trình công cộng trong lòng đất và tuân thủ quy định khác của pháp luật có liên quan.
```

### LDD_2024_D31_K2

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 31, Kho?n 2, ?i?m -
- Article title: Nghĩa vụ chung của người sử dụng đất

Source excerpt:

```text
2. Thực hiện kê khai đăng ký đất đai; thực hiện đầy đủ thủ tục khi chuyển đổi, chuyển nhượng, cho thuê, cho thuê lại, thừa kế, tặng cho quyền sử dụng đất, thế chấp, góp vốn bằng quyền sử dụng đất theo quy định của pháp luật.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_024`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_025

- Query: Theo Luật Kinh doanh bất động sản 2023, Chính phủ quy định chi tiết về trình tự, thủ tục, hồ sơ chuyển nhượng hợp đồng nào?
- Law ID: LKDBDS_2023
- Law name: Luật Kinh doanh bất động sản 2023
- Search law ID: LKDBDS_2023
- Gold chunk IDs: LKDBDS_2023_D52

### LKDBDS_2023_D52

- Unit type: article
- ?i?u/Kho?n/?i?m: ?i?u 52, Kho?n -, ?i?m -
- Article title: Trình tự, thủ tục, hồ sơ chuyển nhượng hợp đồng kinh doanh bất động sản

Source excerpt:

```text
Chính phủ quy định chi tiết về trình tự, thủ tục, hồ sơ chuyển nhượng hợp đồng kinh doanh bất động sản.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_025`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_026

- Query: Khi cÆ¡ quan, tá»• chá»©c bÃ¡n hoáº·c cho thuÃª báº¥t Ä‘á»™ng sáº£n lÃ  tÃ i sáº£n cÃ´ng thÃ¬ trÆ°á»ng há»£p Ä‘Ã³ cÃ³ bá»‹ loáº¡i trá»« khá»i pháº¡m vi Ä‘iá»u chá»‰nh khÃ´ng?
- Law ID: LKDBDS_2023
- Law name: Luật Kinh doanh bất động sản 2023
- Search law ID: null
- Gold chunk IDs: LKDBDS_2023_D1_K2_DB

### LKDBDS_2023_D1_K2_DB

- Unit type: point
- ?i?u/Kho?n/?i?m: ?i?u 1, Kho?n 2, ?i?m b
- Article title: Phạm vi điều chỉnh

Source excerpt:

```text
b) Cơ quan, tổ chức, đơn vị bán, chuyển nhượng, cho thuê bất động sản là tài sản công theo quy định của pháp luật về quản lý, sử dụng tài sản công;
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_026`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_027

- Query: Theo Luáº­t Kinh doanh báº¥t Ä‘á»™ng sáº£n 2023, sÃ n giao dá»‹ch báº¥t Ä‘á»™ng sáº£n lÃ  nÆ¡i diá»…n ra nhá»¯ng giao dá»‹ch nÃ o?
- Law ID: LKDBDS_2023
- Law name: Luật Kinh doanh bất động sản 2023
- Search law ID: LKDBDS_2023
- Gold chunk IDs: LKDBDS_2023_D3_K10

### LKDBDS_2023_D3_K10

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 3, Kho?n 10, ?i?m -
- Article title: Giải thích từ ngữ

Source excerpt:

```text
10. Sàn giao dịch bất động sản là nơi diễn ra các giao dịch về mua bán, chuyển nhượng, cho thuê, cho thuê lại, cho thuê mua bất động sản được thành lập và hoạt động theo quy định của Luật này.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_027`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_028

- Query: MÃ´i giá»›i báº¥t Ä‘á»™ng sáº£n Ä‘Æ°á»£c hiá»ƒu lÃ  viá»‡c lÃ m trung gian cho cÃ¡c bÃªn trong nhá»¯ng giao dá»‹ch nÃ o?
- Law ID: LKDBDS_2023
- Law name: Luật Kinh doanh bất động sản 2023
- Search law ID: null
- Gold chunk IDs: LKDBDS_2023_D3_K11

### LKDBDS_2023_D3_K11

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 3, Kho?n 11, ?i?m -
- Article title: Giải thích từ ngữ

Source excerpt:

```text
11. Môi giới bất động sản là việc làm trung gian cho các bên trong mua bán, chuyển nhượng, cho thuê, cho thuê lại, cho thuê mua bất động sản.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_028`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_029

- Query: Theo Luáº­t Kinh doanh báº¥t Ä‘á»™ng sáº£n 2023, chá»§ Ä‘áº§u tÆ° cÃ³ cáº§n Ä‘Æ°á»£c ngÃ¢n hÃ ng báº£o lÃ£nh trÆ°á»›c khi bÃ¡n nhÃ  á»Ÿ hÃ¬nh thÃ nh trong tÆ°Æ¡ng lai khÃ´ng?
- Law ID: LKDBDS_2023
- Law name: Luật Kinh doanh bất động sản 2023
- Search law ID: LKDBDS_2023
- Gold chunk IDs: LKDBDS_2023_D26_K1

### LKDBDS_2023_D26_K1

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 26, Kho?n 1, ?i?m -
- Article title: Bảo lãnh trong bán, cho thuê mua nhà ở hình thành trong tương lai

Source excerpt:

```text
1. Chủ đầu tư dự án bất động sản trước khi bán, cho thuê mua nhà ở hình thành trong tương lai phải được ngân hàng thương mại trong nước, chi nhánh ngân hàng nước ngoài đang hoạt động hợp pháp tại Việt Nam chấp thuận cấp bảo lãnh cho nghĩa vụ tài chính của chủ đầu tư đối với bên mua, thuê mua nhà ở khi chủ đầu tư không bàn giao nhà ở theo cam kết trong hợp đồng mua bán, thuê mua nhà ở hình thành trong tương lai (sau đây gọi chung là ngân hàng bảo lãnh).

Nghĩa vụ tài chính của chủ đầu tư đối với bên mua, thuê mua nhà ở khi chủ đầu tư không bàn giao nhà ở theo cam kết với bên mua, thuê mua trong hợp đồng mua bán, thuê mua nhà ở hình thành trong tương lai bao gồm số tiền chủ đầu tư đã nhận ứng...
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_029`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_030

- Query: Trong kinh doanh báº¥t Ä‘á»™ng sáº£n, há»£p Ä‘á»“ng dá»‹ch vá»¥ sÃ n giao dá»‹ch vÃ  há»£p Ä‘á»“ng dá»‹ch vá»¥ mÃ´i giá»›i lÃ  cÃ¡c loáº¡i há»£p Ä‘á»“ng nÃ o?
- Law ID: LKDBDS_2023
- Law name: Luật Kinh doanh bất động sản 2023
- Search law ID: null
- Gold chunk IDs: LKDBDS_2023_D44_K2_DA, LKDBDS_2023_D44_K2_DB

### LKDBDS_2023_D44_K2_DA

- Unit type: point
- ?i?u/Kho?n/?i?m: ?i?u 44, Kho?n 2, ?i?m a
- Article title: Hợp đồng trong kinh doanh bất động sản

Source excerpt:

```text
a) Hợp đồng dịch vụ sàn giao dịch bất động sản;
```

### LKDBDS_2023_D44_K2_DB

- Unit type: point
- ?i?u/Kho?n/?i?m: ?i?u 44, Kho?n 2, ?i?m b
- Article title: Hợp đồng trong kinh doanh bất động sản

Source excerpt:

```text
b) Hợp đồng dịch vụ môi giới bất động sản;
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_030`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_031

- Query: Theo Luật Nhà ở 2023, giao dịch về nhà ở bao gồm những hình thức nào?
- Law ID: LNO_2023
- Law name: Luật Nhà ở 2023
- Search law ID: LNO_2023
- Gold chunk IDs: LNO_2023_D159

### LNO_2023_D159

- Unit type: article
- ?i?u/Kho?n/?i?m: ?i?u 159, Kho?n -, ?i?m -
- Article title: Giao dịch về nhà ở

Source excerpt:

```text
Giao dịch về nhà ở bao gồm mua bán, thuê mua, thuê, tặng cho, đổi, thừa kế, thế chấp, góp vốn, cho mượn, cho ở nhờ, ủy quyền quản lý nhà ở.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_031`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_032

- Query: NhÃ  chung cÆ° cÃ³ Ä‘áº·c Ä‘iá»ƒm gÃ¬ vá» sá»‘ táº§ng, cÄƒn há»™ vÃ  pháº§n sá»Ÿ há»¯u chung riÃªng?
- Law ID: LNO_2023
- Law name: Luật Nhà ở 2023
- Search law ID: null
- Gold chunk IDs: LNO_2023_D2_K3

### LNO_2023_D2_K3

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 2, Kho?n 3, ?i?m -
- Article title: Giải thích từ ngữ

Source excerpt:

```text
3. Nhà chung cư là nhà ở có từ 02 tầng trở lên, có nhiều căn hộ, có lối đi, cầu thang chung, có phần sở hữu riêng, phần sở hữu chung và hệ thống công trình hạ tầng sử dụng chung cho gia đình, cá nhân, tổ chức, bao gồm nhà chung cư được xây dựng với mục đích để ở và nhà chung cư được xây dựng có mục đích sử dụng hỗn hợp.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_032`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_033

- Query: Theo Luáº­t NhÃ  á»Ÿ 2023, nhá»¯ng nhÃ³m chá»§ thá»ƒ nÃ o Ä‘Æ°á»£c sá»Ÿ há»¯u nhÃ  á»Ÿ táº¡i Viá»‡t Nam?
- Law ID: LNO_2023
- Law name: Luật Nhà ở 2023
- Search law ID: LNO_2023
- Gold chunk IDs: LNO_2023_D8_K1_DA, LNO_2023_D8_K1_DB, LNO_2023_D8_K1_DC

### LNO_2023_D8_K1_DA

- Unit type: point
- ?i?u/Kho?n/?i?m: ?i?u 8, Kho?n 1, ?i?m a
- Article title: Đối tượng và điều kiện được sở hữu nhà ở tại Việt Nam

Source excerpt:

```text
a) Tổ chức, cá nhân trong nước;
```

### LNO_2023_D8_K1_DB

- Unit type: point
- ?i?u/Kho?n/?i?m: ?i?u 8, Kho?n 1, ?i?m b
- Article title: Đối tượng và điều kiện được sở hữu nhà ở tại Việt Nam

Source excerpt:

```text
b) Người Việt Nam định cư ở nước ngoài theo quy định của pháp luật về quốc tịch;
```

### LNO_2023_D8_K1_DC

- Unit type: point
- ?i?u/Kho?n/?i?m: ?i?u 8, Kho?n 1, ?i?m c
- Article title: Đối tượng và điều kiện được sở hữu nhà ở tại Việt Nam

Source excerpt:

```text
c) Tổ chức, cá nhân nước ngoài theo quy định tại khoản 1 Điều 17 của Luật này.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_033`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_034

- Query: KhÃ´ng Ä‘Ã³ng kinh phÃ­ báº£o trÃ¬ hoáº·c sá»­ dá»¥ng sai quá»¹ báº£o trÃ¬ pháº§n sá»Ÿ há»¯u chung nhÃ  chung cÆ° cÃ³ bá»‹ cáº¥m khÃ´ng?
- Law ID: LNO_2023
- Law name: Luật Nhà ở 2023
- Search law ID: null
- Gold chunk IDs: LNO_2023_D3_K8_DA

### LNO_2023_D3_K8_DA

- Unit type: point
- ?i?u/Kho?n/?i?m: ?i?u 3, Kho?n 8, ?i?m a
- Article title: Các hành vi bị nghiêm cấm

Source excerpt:

```text
a) Không đóng kinh phí bảo trì phần sở hữu chung của nhà chung cư (sau đây gọi chung là kinh phí bảo trì); quản lý, sử dụng kinh phí quản lý vận hành, kinh phí bảo trì không đúng quy định của pháp luật về nhà ở;
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_034`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_035

- Query: Theo Luáº­t NhÃ  á»Ÿ 2023, cÃ¡ nhÃ¢n cÃ³ quyá»n cÃ³ chá»— á»Ÿ thÃ´ng qua nhá»¯ng hÃ¬nh thá»©c nÃ o?
- Law ID: LNO_2023
- Law name: Luật Nhà ở 2023
- Search law ID: LNO_2023
- Gold chunk IDs: LNO_2023_D6_K1

### LNO_2023_D6_K1

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 6, Kho?n 1, ?i?m -
- Article title: Quyền có chỗ ở và quyền sở hữu nhà ở

Source excerpt:

```text
1. Cá nhân có quyền có chỗ ở thông qua việc đầu tư xây dựng, mua, thuê mua, thuê, nhận tặng cho, nhận thừa kế, nhận góp vốn, nhận đổi, mượn, ở nhờ, quản lý nhà ở theo ủy quyền và hình thức khác theo quy định của pháp luật.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_035`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_036

- Query: PhÃ¡t triá»ƒn nhÃ  á»Ÿ lÃ  Ä‘áº§u tÆ° xÃ¢y má»›i, xÃ¢y dá»±ng láº¡i hoáº·c cáº£i táº¡o Ä‘á»ƒ lÃ m gÃ¬?
- Law ID: LNO_2023
- Law name: Luật Nhà ở 2023
- Search law ID: null
- Gold chunk IDs: LNO_2023_D2_K15

### LNO_2023_D2_K15

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 2, Kho?n 15, ?i?m -
- Article title: Giải thích từ ngữ

Source excerpt:

```text
15. Phát triển nhà ở là việc đầu tư xây dựng mới, xây dựng lại hoặc cải tạo nhà ở làm tăng diện tích nhà ở.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_036`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_037

- Query: Theo Luật Tương trợ tư pháp về hình sự 2025, Luật này điều chỉnh những nội dung nào giữa Việt Nam với nước ngoài?
- Law ID: LTTPHS_2025
- Law name: Luật Tương trợ tư pháp về hình sự 2025
- Search law ID: LTTPHS_2025
- Gold chunk IDs: LTTPHS_2025_D1

### LTTPHS_2025_D1

- Unit type: article
- ?i?u/Kho?n/?i?m: ?i?u 1, Kho?n -, ?i?m -
- Article title: Phạm vi điều chỉnh

Source excerpt:

```text
Luật này quy định nguyên tắc, thẩm quyền, trình tự, thủ tục thực hiện tương trợ tư pháp về hình sự giữa Việt Nam với nước ngoài; trách nhiệm của các cơ quan nhà nước Việt Nam trong tương trợ tư pháp về hình sự.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_037`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_038

- Query: CÆ¡ quan trung Æ°Æ¡ng cá»§a Viá»‡t Nam trong tÆ°Æ¡ng trá»£ tÆ° phÃ¡p vá» hÃ¬nh sá»± lÃ  cÆ¡ quan nÃ o?
- Law ID: LTTPHS_2025
- Law name: Luật Tương trợ tư pháp về hình sự 2025
- Search law ID: null
- Gold chunk IDs: LTTPHS_2025_D6_K1

### LTTPHS_2025_D6_K1

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 6, Kho?n 1, ?i?m -
- Article title: Cơ quan trung ương của nước Cộng hòa xã hội chủ nghĩa Việt Nam trong tương trợ tư pháp về hình sự

Source excerpt:

```text
1. Viện kiểm sát nhân dân tối cao là Cơ quan trung ương của nước Cộng hòa xã hội chủ nghĩa Việt Nam trong tương trợ tư pháp về hình sự.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_038`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_039

- Query: Theo Luáº­t TÆ°Æ¡ng trá»£ tÆ° phÃ¡p vá» hÃ¬nh sá»± 2025, há»“ sÆ¡ yÃªu cáº§u cá»§a Viá»‡t Nam gá»“m vÄƒn báº£n yÃªu cáº§u vÃ  tÃ i liá»‡u nÃ o khÃ¡c?
- Law ID: LTTPHS_2025
- Law name: Luật Tương trợ tư pháp về hình sự 2025
- Search law ID: LTTPHS_2025
- Gold chunk IDs: LTTPHS_2025_D19_K1_DA, LTTPHS_2025_D19_K1_DB

### LTTPHS_2025_D19_K1_DA

- Unit type: point
- ?i?u/Kho?n/?i?m: ?i?u 19, Kho?n 1, ?i?m a
- Article title: Hồ sơ yêu cầu tương trợ tư pháp về hình sự của Việt Nam

Source excerpt:

```text
a) Văn bản yêu cầu tương trợ tư pháp về hình sự của Việt Nam quy định tại khoản 1 Điều 20 của Luật này;
```

### LTTPHS_2025_D19_K1_DB

- Unit type: point
- ?i?u/Kho?n/?i?m: ?i?u 19, Kho?n 1, ?i?m b
- Article title: Hồ sơ yêu cầu tương trợ tư pháp về hình sự của Việt Nam

Source excerpt:

```text
b) Tài liệu khác (nếu có).
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_039`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_040

- Query: Náº¿u Viá»‡t Nam vÃ  nÆ°á»›c ngoÃ i khÃ´ng cÃ¹ng Ä‘iá»u Æ°á»›c quá»‘c táº¿ thÃ¬ há»“ sÆ¡ yÃªu cáº§u pháº£i kÃ¨m báº£n dá»‹ch sang ngÃ´n ngá»¯ nÃ o?
- Law ID: LTTPHS_2025
- Law name: Luật Tương trợ tư pháp về hình sự 2025
- Search law ID: null
- Gold chunk IDs: LTTPHS_2025_D8_K2

### LTTPHS_2025_D8_K2

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 8, Kho?n 2, ?i?m -
- Article title: Ngôn ngữ trong hồ sơ yêu cầu tương trợ tư pháp về hình sự

Source excerpt:

```text
2. Trường hợp Việt Nam và nước ngoài không cùng là thành viên của điều ước quốc tế về tương trợ tư pháp về hình sự thì hồ sơ yêu cầu tương trợ tư pháp về hình sự phải kèm theo bản dịch ra ngôn ngữ của nước được yêu cầu hoặc ngôn ngữ khác mà nước được yêu cầu chấp nhận.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_040`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_041

- Query: Theo Luáº­t TÆ°Æ¡ng trá»£ tÆ° phÃ¡p vá» hÃ¬nh sá»± 2025, Viá»‡n kiá»ƒm sÃ¡t nhÃ¢n dÃ¢n tá»‘i cao kiá»ƒm tra tÃ­nh há»£p lá»‡ cá»§a há»“ sÆ¡ yÃªu cáº§u trong bao lÃ¢u?
- Law ID: LTTPHS_2025
- Law name: Luật Tương trợ tư pháp về hình sự 2025
- Search law ID: LTTPHS_2025
- Gold chunk IDs: LTTPHS_2025_D21_K3

### LTTPHS_2025_D21_K3

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 21, Kho?n 3, ?i?m -
- Article title: Lập, gửi yêu cầu tương trợ tư pháp về hình sự

Source excerpt:

```text
3. Trong thời hạn 10 ngày kể từ ngày nhận được hồ sơ yêu cầu, Viện kiểm sát nhân dân tối cao vào sổ thụ lý, kiểm tra tính hợp lệ của hồ sơ. Trường hợp hồ sơ hợp lệ, Viện kiểm sát nhân dân tối cao gửi hồ sơ cho cơ quan có thẩm quyền của nước ngoài theo quy định của điều ước quốc tế mà nước Cộng hòa xã hội chủ nghĩa Việt Nam là thành viên hoặc chuyển cho Bộ Ngoại giao trong trường hợp Việt Nam và nước ngoài không cùng là thành viên của điều ước quốc tế hoặc điều ước quốc tế mà nước Cộng hòa xã hội chủ nghĩa Việt Nam là thành viên quy định chuyển hồ sơ qua kênh ngoại giao, đồng thời thông báo cho cơ quan lập yêu cầu biết. Trường hợp hồ sơ không hợp lệ, Viện kiểm sát nhân dân tối cao trả lại hồ...
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_041`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_042

- Query: Khi triá»‡u táº­p ngÆ°á»i lÃ m chá»©ng tá»« Viá»‡t Nam sang nÆ°á»›c yÃªu cáº§u, vÄƒn báº£n yÃªu cáº§u pháº£i gá»­i trÆ°á»›c bao lÃ¢u?
- Law ID: LTTPHS_2025
- Law name: Luật Tương trợ tư pháp về hình sự 2025
- Search law ID: null
- Gold chunk IDs: LTTPHS_2025_D32_K1

### LTTPHS_2025_D32_K1

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 32, Kho?n 1, ?i?m -
- Article title: Thực hiện yêu cầu về tống đạt, giao, gửi giấy triệu tập

Source excerpt:

```text
1. Trường hợp triệu tập người làm chứng, người giám định hoặc những người có liên quan khác đang có mặt tại Việt Nam sang nước yêu cầu, cơ quan có thẩm quyền của nước yêu cầu gửi văn bản yêu cầu kèm theo giấy triệu tập (nếu có) cho Viện kiểm sát nhân dân tối cao chậm nhất là 90 ngày trước ngày người đó phải có mặt tại nước yêu cầu. Trong trường hợp khẩn cấp, Viện kiểm sát nhân dân tối cao có thể không áp dụng thời hạn này.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_042`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_043

- Query: Theo Luật Xây dựng 2014, Luật này quy định về quyền, nghĩa vụ và quản lý nhà nước trong hoạt động nào?
- Law ID: LXD_2014
- Law name: Luật Xây dựng 2014
- Search law ID: LXD_2014
- Gold chunk IDs: LXD_2014_D1

### LXD_2014_D1

- Unit type: article
- ?i?u/Kho?n/?i?m: ?i?u 1, Kho?n -, ?i?m -
- Article title: Phạm vi điều chỉnh

Source excerpt:

```text
Luật này quy định về quyền, nghĩa vụ, trách nhiệm của cơ quan, tổ chức, cá nhân và quản lý nhà nước trong hoạt động đầu tư xây dựng.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_043`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_044

- Query: Chá»§ Ä‘áº§u tÆ° pháº£i mua báº£o hiá»ƒm cÃ´ng trÃ¬nh trong thá»i gian xÃ¢y dá»±ng Ä‘á»‘i vá»›i loáº¡i cÃ´ng trÃ¬nh nÃ o?
- Law ID: LXD_2014
- Law name: Luật Xây dựng 2014
- Search law ID: null
- Gold chunk IDs: LXD_2014_D9_K2_DA

### LXD_2014_D9_K2_DA

- Unit type: point
- ?i?u/Kho?n/?i?m: ?i?u 9, Kho?n 2, ?i?m a
- Article title: Bảo hiểm trong hoạt động đầu tư xây dựng

Source excerpt:

```text
a) Chủ đầu tư mua bảo hiểm công trình trong thời gian xây dựng đối với công trình có ảnh hưởng đến an toàn cộng đồng, môi trường, công trình có yêu cầu kỹ thuật đặc thù, điều kiện thi công xây dựng phức tạp;
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_044`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_045

- Query: Theo Luáº­t XÃ¢y dá»±ng 2014, khá»Ÿi cÃ´ng xÃ¢y dá»±ng cÃ´ng trÃ¬nh khi chÆ°a Ä‘á»§ Ä‘iá»u kiá»‡n cÃ³ bá»‹ cáº¥m khÃ´ng?
- Law ID: LXD_2014
- Law name: Luật Xây dựng 2014
- Search law ID: LXD_2014
- Gold chunk IDs: LXD_2014_D12_K2

### LXD_2014_D12_K2

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 12, Kho?n 2, ?i?m -
- Article title: Các hành vi bị nghiêm cấm

Source excerpt:

```text
2. Khởi công xây dựng công trình khi chưa đủ điều kiện khởi công theo quy định của Luật này.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_045`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_046

- Query: CÃ´ng trÃ¬nh hoÃ n thÃ nh chá»‰ Ä‘Æ°á»£c Ä‘Æ°a vÃ o khai thÃ¡c sau khi Ä‘Ã¡p á»©ng yÃªu cáº§u nghiá»‡m thu nÃ o?
- Law ID: LXD_2014
- Law name: Luật Xây dựng 2014
- Search law ID: null
- Gold chunk IDs: LXD_2014_D123_K2

### LXD_2014_D123_K2

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 123, Kho?n 2, ?i?m -
- Article title: Nghiệm thu công trình xây dựng

Source excerpt:

```text
2. Hạng mục công trình, công trình xây dựng hoàn thành chỉ được phép đưa vào khai thác, sử dụng sau khi được nghiệm thu bảo đảm yêu cầu của thiết kế xây dựng, tiêu chuẩn áp dụng, quy chuẩn kỹ thuật cho công trình, quy định về quản lý sử dụng vật liệu xây dựng và được nghiệm thu theo quy định của Luật này.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_046`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_047

- Query: Theo Luáº­t XÃ¢y dá»±ng 2014, nghiá»‡m thu cÃ´ng trÃ¬nh xÃ¢y dá»±ng bao gá»“m nghiá»‡m thu cÃ´ng viá»‡c vÃ  nghiá»‡m thu hoÃ n thÃ nh gÃ¬?
- Law ID: LXD_2014
- Law name: Luật Xây dựng 2014
- Search law ID: LXD_2014
- Gold chunk IDs: LXD_2014_D123_K1_DA, LXD_2014_D123_K1_DB

### LXD_2014_D123_K1_DA

- Unit type: point
- ?i?u/Kho?n/?i?m: ?i?u 123, Kho?n 1, ?i?m a
- Article title: Nghiệm thu công trình xây dựng

Source excerpt:

```text
a) Nghiệm thu công việc xây dựng trong quá trình thi công và nghiệm thu các giai đoạn chuyển bước thi công khi cần thiết;
```

### LXD_2014_D123_K1_DB

- Unit type: point
- ?i?u/Kho?n/?i?m: ?i?u 123, Kho?n 1, ?i?m b
- Article title: Nghiệm thu công trình xây dựng

Source excerpt:

```text
b) Nghiệm thu hoàn thành hạng mục công trình, hoàn thành công trình xây dựng để đưa vào khai thác, sử dụng.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_047`. Multi-gold cases list each chunk needed for the separate parts of the question.

## eval_048

- Query: Khi bÃ n giao cÃ´ng trÃ¬nh, nhÃ  tháº§u thi cÃ´ng pháº£i giao nhá»¯ng tÃ i liá»‡u váº­n hÃ nh vÃ  báº£o trÃ¬ nÃ o cho chá»§ Ä‘áº§u tÆ°?
- Law ID: LXD_2014
- Law name: Luật Xây dựng 2014
- Search law ID: null
- Gold chunk IDs: LXD_2014_D124_K3

### LXD_2014_D124_K3

- Unit type: clause
- ?i?u/Kho?n/?i?m: ?i?u 124, Kho?n 3, ?i?m -
- Article title: Bàn giao công trình xây dựng

Source excerpt:

```text
3. Khi bàn giao công trình xây dựng, nhà thầu thi công xây dựng phải giao cho chủ đầu tư các tài liệu gồm bản vẽ hoàn công, quy trình hướng dẫn vận hành, quy trình bảo trì công trình, danh mục các thiết bị, phụ tùng, vật tư dự trữ thay thế và các tài liệu cần thiết khác có liên quan.
```

Why this gold is correct:

The selected chunk content directly answers the query by containing the rule, definition, condition, authority, right, obligation, or time limit asked in `eval_048`. Multi-gold cases list each chunk needed for the separate parts of the question.
