# 发布包装 QA —— 《赤壁赋》（chibifu-g1chn-20261019）

生成时间：2026-10-21 00:20（本地）；最后更新 2026-10-21 03:48（公众号草稿已创建、星球已发布）

## 发布包构成（outputs/social/）

| 产物 | 状态 | 证据 |
|---|---|---|
| `video_9x16.mp4` | ✅ | 1080×1920，142.033s，由 BGM 版 16:9 母版包装（幻灯片区 1080×608 完整 16:9 居中，音频 `-c:a copy`），sha256 aa287c6d…605e1e4 |
| `xiaohongshu/copy.txt` | ✅ | 3 行；摘要段 ≈21 汉字（≤50）；标签恰 5 个 |
| `douyin/copy.txt` | ✅ | 3 行；摘要段 ≈30 汉字；标签恰 5 个 |
| `weixin_channels/copy.txt` | ✅ | 3 行；摘要段 ≈35 汉字；标签恰 5 个 |
| `wechat_official_account/cover.jpg` | ✅ | 900×383，59,093 B（≤64 KiB） |
| `wechat_official_account/slides/slide_01..25.jpg` | ✅ | 25 张（= 当前 PPT 实际页数），1600×900，全部 <1 MiB，来自最终版 PDF |
| `wechat_official_account/article.md/.html` | ✅ | wechat-ios-showcase@1.0；标题《赤壁赋》高一上册语文动态课件AI赋能；结构：课程信息→课件简介→AI视频→HTML互动→PPT视觉展示→资料清单→星球入口；无 `<video>`、无标签、无内部说明 |
| `wechat_official_account/publish_result.json` | ✅ | 草稿已创建，详见下节 |

## 公众号草稿：已创建（40164 已解除）

- 前提：把出口 IP `182.123.103.118` 加入公众号后台 IP 白名单后，`get_access_token` 恢复正常。
- 重跑 `publish_wechat_official.py --mode draft` 结果：
  - `status: draft_created`
  - `draft_media_id: kLU5-QMfMMKHtGm0e__gUCHIxTyVUa3hD63bcFJtYx1wh0WN7KFqgLeCuaafmKz4`
  - `cover_media_id: kLU5-QMfMMKHtGm0e__gUKMU_JiHOOjhRr1UtWdxc25_OzZF85T4n5EQwTnEMtap`
  - 25 张幻灯片图 + 封面 + 星球卡共 26 张全部上传并替换为微信 CDN（article.html 内已无本地 src 残留）
  - 小程序短码 `#小程序://知识星球/AeKfWrJ03JXyNSq` 已插入（`miniprogram_code_inserted: true`）
- **未正式发布**：按 SKILL 门禁，正式发布（`--mode publish`）须用户明确要求且账号具备 freepublish 权限。当前草稿在公众号草稿箱，可后台手动发布或授权后自动化。
- 踩坑记录：`publish_wechat_official.py` 的 `asset_root` 默认为 `--article-file` 所在目录，因此 `build_wechat_article.py --planet-qr` 必须传**与 article.html 同级的文件名**（如 `planet_card.jpg`）；传带目录前缀的相对路径会被二次拼接成 `…/wechat_official_account/outputs/social/wechat_official_account/planet_card.jpg` 而找不到文件。

## 知识星球：已发布（按用户明确要求提前触发）

- topic_id `55521544852855844`
- 链接 https://wx.zsxq.com/group/48885448528888/topic/55521544852855844
- 星球「一堂微课」（group-id 48885448528888），2026-10-21 03:48 创建，5 个附件全部上传成功：封面图.jpg / 可编辑课件.pptx / 互动练习.html / 教学设计.docx / AI导入短片.zip
- 文案 `outputs/social/zsxq/copy.txt`：纯文本，无 Markdown 符号、无 emoji、无品牌行，列举用 ①②③④，含教材信息行
- **触发依据**：SKILL 第 7 条「用户明确要求该课提前发布时，可按该次指令执行，不改变后续默认顺序」。本次用户将「知识星球发布」列为待办项，故在公众号草稿态下提前发布；后续课程仍按默认顺序（公众号 publish_status=0 后触发）。
- 已回读 `topic +detail` 核实：正文、5 附件、时间戳一致；manifest 已记录 topic_id，不会重复发帖。
- 平台行为（非缺陷）：即便用 `--text`，星球服务端仍会把正文里的《赤壁赋》书名号自动转成「查找图书」链接元素，属平台固有渲染，不影响内容。

## 轻量版课件（为适配星球 50MB 附件上限）

- 星球单附件上限 **50 MB**，原课件 51.92 MB 超限，首次发帖失败（`code=13405`，4 个附件已传但 pptx 被拒，主题整体未创建）。
- 用 `working/make_light_pptx.py` 生成轻量版 **39.28 MB**：仅把 PNG 降到 1920 宽（PPT 页宽 13.33in ⇒ 144dpi，足够投影），**不量化、不改扩展名、不动任何 .rels / [Content_Types].xml**，保留 `ppt/media/media1.mp4` 内嵌视频。
- 完整性复核：25 页 / 323 对象 / 208 文本框 / 26 图片 / 媒体 `ai-video-01-1080p.mp4` 均在，90 个 part 无缺失。

## 备注

- BGM：`assets/bgm/bgm-y2k-elevator.mp3`（Kevin MacLeod, CC-BY 4.0），视频简介/片尾需署名一行。
- 三个手动平台共用唯一 `video_9x16.mp4`，各平台目录内无视频副本。
