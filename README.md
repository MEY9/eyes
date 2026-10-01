# eyes：教育视觉产品工作台

这是一个面向教育视觉产品的长期仓库。第一阶段只做“教育课件 PPT 产品”，后续再扩展希沃、万彩动画和 HTML 课件。

## 当前目标

把教材 PDF 转换成可售卖的教育视觉产品：

```text
教材 PDF
→ 内容与教学目标分析
→ PPT 故事板
→ AI 图片与视频
→ 可编辑 PPTX
→ 可选 HTML 互动环节
→ 商品演示与交付包
```

## 仓库结构

```text
agents/
  education-ppt-product/       教育 PPT 产品主 Agent 定义
skills/
  education-ppt-product/       可被 Codex 调用的项目 Skill
products/
  education-ppt/                PPT 产品规范、SKU 与交付结构
materials/
  textbooks/                    本地教材 PDF，默认不提交远程
projects/                      具体课程项目
logs/                           任务记录、复盘和版本决策
scripts/
  sync-codex-assets.sh          将仓库 Skill 同步到本机 Codex
```

## 使用方式

启动 PPT 产品 Agent：

```text
请使用 education-ppt-product Agent，从教材 PDF 分析开始。
```

显式调用 Skill：

```text
$education-ppt-product
```

## 本地与远程同步原则

仓库中的 `agents/` 和 `skills/` 是源文件；本机 Codex skills 目录是运行入口。修改 Skill 后先同步本机，再提交并推送远程：

```bash
export CODEX_SKILLS_DIR="/Users/sk/.codex/skills"
./scripts/sync-codex-assets.sh
git add agents skills products scripts README.md .gitignore
git commit -m "建立教育PPT产品Agent与Skill"
git push -u origin main
```

如果更换电脑，只需要拉取仓库，设置新的 `CODEX_SKILLS_DIR`，再运行同步脚本。

## 数据安全和版权

- 教材 PDF、客户资料、未授权图片和内部资料默认只保留在本地。
- 只有确认可以公开、商用或用于交付的素材才进入远程仓库。
- AI 生成内容要记录生成工具、日期、参考图、后处理和授权判断。
- 医学、法律和安全类内容必须保留来源和专家审核记录。
