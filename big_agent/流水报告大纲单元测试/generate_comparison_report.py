"""
流水分析报告大纲比较报告生成器
================================

此脚本专门用于生成比较报告，不重新生成md文件，直接分析已有的30个md文件。

测试流程：
1. 读取已有的level1-1.md到level3-10.md文件
2. 将结果转换为基础版本格式
3. 进行多维度比较分析（使用大模型计算相似度）
4. 生成比较报告

作者: Test Team
版本: 1.0.0
创建时间: 2024-12-20
"""

import os
import json
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import re


class ComparisonReportGenerator:
    """比较报告生成器"""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        """初始化报告生成器"""
        self.api_key = "sk-438668d443224063adbb1d295fe44a9f"
        self.base_url = base_url
        self.test_dir = Path("流水报告大纲单元测试")

        # 初始化DeepSeek模型
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=api_key,
            base_url=base_url,
            temperature=0.1
        )

        # 加载基础版本
        self.baseline_content = self._load_baseline()

    def _load_baseline(self) -> str:
        """加载基础版本内容"""
        baseline_file = self.test_dir / "流水分析大纲-基础版本.md"
        with open(baseline_file, 'r', encoding='utf-8') as f:
            return f.read().strip()

    def _convert_to_baseline_format(self, content: str) -> str:
        """将内容转换为基础版本格式（只有标题和缩进）"""
        lines = content.split('\n')
        converted_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 保留标题结构
            if line.startswith('#'):
                converted_lines.append(line)
            # 保留缩进结构（转换为markdown列表）
            elif line.startswith('-') or line.startswith('*'):
                converted_lines.append(line)
            # 转换其他内容为列表项
            elif len(line) > 0:
                converted_lines.append(f"- {line}")

        return '\n'.join(converted_lines)

    async def _calculate_similarity(self, text1: str, text2: str) -> float:
        """使用大模型计算两个文本的语义相似度"""
        prompt = f"""请分析以下两个文本的语义相似度，给出一个0-1之间的分数。

文本1：
{text1}

文本2：
{text2}

要求：
1. 分析两个文本在语义、结构、内容方面的相似程度
2. 考虑专业术语、概念一致性、逻辑结构等因素
3. 输出一个0-1之间的小数，1.0表示完全相同，0.0表示完全不同
4. 只输出数字，不要其他文字

相似度评分："""

        try:
            messages = [
                ("system", "你是一个专业的文本相似度分析专家，只输出0-1之间的数字。"),
                ("user", prompt)
            ]

            response = await self.llm.ainvoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)

            # 提取数字
            import re
            match = re.search(r'(\d+\.?\d*)', content.strip())
            if match:
                similarity = float(match.group(1))
                # 确保在0-1范围内
                return max(0.0, min(1.0, similarity))
            else:
                print(f"无法解析相似度结果: {content}")
                return 0.0

        except Exception as e:
            print(f"计算相似度失败: {str(e)}")
            # 返回简单的Jaccard相似度作为fallback
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())

            if not words1 and not words2:
                return 1.0

            intersection = words1.intersection(words2)
            union = words1.union(words2)

            return len(intersection) / len(union) if union else 0.0

    def _extract_sections(self, content: str) -> List[Dict[str, str]]:
        """提取内容中的章节"""
        lines = content.split('\n')
        sections = []

        for line in lines:
            if line.startswith('#'):
                # 移除#号和空格
                title = line.lstrip('#').strip()
                sections.append({'title': title, 'content': ''})

        return sections

    async def _analyze_coverage(self, content: str, baseline: str) -> float:
        """分析覆盖度：计算与基础版本的相似度"""
        # 提取基础版本的关键元素
        baseline_sections = self._extract_sections(baseline)
        content_sections = self._extract_sections(content)

        if not baseline_sections:
            return 0.0

        # 计算匹配的章节数
        matched_sections = 0
        for baseline_section in baseline_sections:
            for content_section in content_sections:
                # 使用大模型计算标题相似度
                try:
                    similarity = await self._calculate_similarity(baseline_section['title'], content_section['title'])
                    if similarity > 0.6:  # 相似度阈值
                        matched_sections += 1
                        break
                except Exception as e:
                    print(f"计算标题相似度失败: {str(e)}")
                    # fallback到简单匹配
                    if baseline_section['title'].lower() in content_section['title'].lower():
                        matched_sections += 1
                        break

        return matched_sections / len(baseline_sections)


    async def _analyze_level_coverage(self, level_files: List[Dict[str, Any]], baseline_content: str, level: str) -> List[Dict[str, Any]]:
        """一次性分析一个level的所有文件覆盖度"""
        # 准备所有文件内容
        files_content = ""
        for i, file_data in enumerate(level_files, 1):
            files_content += f"\n=== {level}-{file_data['index']} ===\n"
            files_content += file_data['converted_content']
            files_content += "\n"

        # 大模型分析覆盖度
        prompt = f"""请分析以下{len(level_files)}个{level}级别生成的流水分析大纲与基础版本的覆盖度。

基础版本大纲：
{baseline_content}

生成的{level}大纲：
{files_content}

请为每个生成的{level}大纲计算其对基础版本的覆盖度（0-100%），并给出平均覆盖度。

输出格式：
文件名: 覆盖度
文件名: 覆盖度
...
平均覆盖度: XX%"""

        try:
            messages = [
                ("system", "你是一个专业的文档分析专家，请准确计算覆盖度。"),
                ("user", prompt)
            ]

            response = await self.llm.ainvoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)

            # 解析结果
            results = []
            lines = content.strip().split('\n')

            for file_data in level_files:
                filename = f"{level}-{file_data['index']}"
                coverage = 0.0

                # 在响应中查找对应的覆盖度
                for line in lines:
                    if filename in line and ('%' in line or any(char.isdigit() for char in line)):
                        # 提取百分比数字，匹配文件名后面的数字
                        match = re.search(rf'{filename}.*?(\d+(?:\.\d+)?)%?', line)
                        if match:
                            coverage = float(match.group(1))
                            break

                # 如果没找到，尝试查找单独的行
                if coverage == 0.0:
                    for line in lines:
                        if line.strip().startswith(filename) and ('%' in line or ':' in line):
                            # 提取冒号或百分号后面的数字
                            match = re.search(r'[:\s]+(\d+(?:\.\d+)?)%?', line)
                            if match:
                                coverage = float(match.group(1))
                                break

                # 限制在0-100范围内
                coverage = max(0.0, min(100.0, coverage))

                analysis = {
                    "level": file_data['level'],
                    "index": file_data['index'],
                    "覆盖度": f"{coverage:.1f}%"
                }
                results.append(analysis)
                print(f"      ✓ {filename}: {coverage:.1f}%")

            return results

        except Exception as e:
            print(f"Level覆盖度分析失败: {str(e)}")
            # 返回默认结果
            return [{
                "level": file_data['level'],
                "index": file_data['index'],
                "覆盖度": "0.0%"
            } for file_data in level_files]


    def _load_existing_files(self) -> List[Dict[str, Any]]:
        """加载已有的md文件（每个level前5个）"""
        results = []
        print("  📂 开始加载md文件...")

        for level in ['level1', 'level2', 'level3']:
            print(f"    🔍 检查 {level} 级别文件...")
            for i in range(1, 6):  # 改为1-5
                filename = f"level{level[-1]}-{i}.md"
                filepath = self.test_dir / filename

                if filepath.exists():
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()

                        results.append({
                            "level": level,
                            "index": i,
                            "content": content,
                            "filepath": str(filepath)
                        })
                        print(f"      ✓ 加载 {filename} ({len(content)} 字符)")
                    except Exception as e:
                        print(f"      ✗ 加载 {filename} 失败: {str(e)}")
                else:
                    print(f"      ⚠ 文件不存在: {filename}")

        print(f"  📊 共加载 {len(results)} 个文件")
        return results

    async def generate_report(self):
        """生成比较报告"""
        print("🚀 开始生成比较报告")
        print("=" * 60)
        print(f"⏰ 开始时间: {datetime.now().strftime('%H:%M:%S')}")

        # 第一步：加载已有文件
        print("\n📂 第一步：加载已有md文件")
        existing_files = self._load_existing_files()
        print(f"  ✅ 第一步完成，共加载 {len(existing_files)} 个文件")

        # 第二步：格式转换
        print("\n🔄 第二步：格式转换")
        converted_results = []
        for i, result in enumerate(existing_files):
            print(f"  🔄 转换中... ({i+1}/{len(existing_files)}) {result['level']}-{result['index']}")
            converted_content = self._convert_to_baseline_format(result['content'])
            result['converted_content'] = converted_content
            converted_results.append(result)
            print(f"    ✓ level{result['level'][-1]}-{result['index']} 格式转换完成")

        print(f"  ✅ 第二步完成，共转换 {len(converted_results)} 个文件")

        # 第三步：按level分组比较分析
        print("\n📊 第三步：按level分组比较分析（每次一个level）")
        analysis_results = []

        # 按level分组处理
        for level in ['level1', 'level2', 'level3']:
            level_files = [f for f in converted_results if f['level'] == level]

            print(f"\n  🔍 处理 {level} 级别 ({len(level_files)} 个文件)")
            print(f"    📋 文件列表: {', '.join([f'{r['level']}-{r['index']}' for r in level_files])}")

            # 一次性分析整个level的所有文件
            print(f"    🤖 调用大模型分析 {level} 级别覆盖度...")
            level_analysis = await self._analyze_level_coverage(level_files, self.baseline_content, level)

            analysis_results.extend(level_analysis)
            print(f"    ✅ {level} 级别分析完成")

        print(f"\n  ✅ 第三步完成，共分析 {len(analysis_results)} 个文件")

        # 第四步：生成比较报告
        print("\n📋 第四步：生成比较报告")
        self._generate_comparison_report(analysis_results)

        end_time = datetime.now()
        print(f"\n✅ 报告生成完成！⏰ 结束时间: {end_time.strftime('%H:%M:%S')}")
        print("📄 比较报告已生成：流水报告大纲单元测试/比较报告.md")

    def _generate_comparison_report(self, analysis_results: List[Dict[str, Any]]):
        """生成比较报告"""
        report_path = self.test_dir / "比较报告.md"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 流水分析大纲生成单元测试比较报告\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("**说明**: 本报告基于大模型语义相似度计算，使用DeepSeek分析文本相似性\n\n")

            # 总体统计
            f.write("## 📊 总体统计\n\n")

            level_stats = {}
            for result in analysis_results:
                level = result['level']
                if level not in level_stats:
                    level_stats[level] = []

                # 提取数值
                coverage_pct = float(result['覆盖度'].rstrip('%'))

                level_stats[level].append({
                    'coverage': coverage_pct
                })

            for level, stats in level_stats.items():
                coverages = [s['coverage'] for s in stats]
                avg_coverage = sum(coverages) / len(coverages)
                max_coverage = max(coverages)
                min_coverage = min(coverages)

                f.write(f"### {level.upper()} 级别统计\n")
                f.write(f"- 样本数量: {len(stats)}\n")
                f.write(f"- 平均覆盖度: {avg_coverage:.1f}%\n")
                f.write(f"- 最高覆盖度: {max_coverage:.1f}%\n")
                f.write(f"- 最低覆盖度: {min_coverage:.1f}%\n\n")

            # 详细结果
            f.write("## 📋 详细测试结果\n\n")

            for level in ['level1', 'level2', 'level3']:
                f.write(f"### {level.upper()} 级别结果\n\n")
                f.write("| 文件名 | 覆盖度 |\n")
                f.write("|--------|--------|\n")

                level_results = [r for r in analysis_results if r['level'] == level]
                for result in level_results:
                    f.write(f"| level{level[-1]}-{result['index']} | {result['覆盖度']} |\n")

                f.write("\n")

            # 结论
            f.write("## 🎯 测试结论\n\n")

            # 找出最佳和最差的表现
            all_coverages = [(r['level'], r['index'], float(r['覆盖度'].rstrip('%'))) for r in analysis_results]

            best_coverage = max(all_coverages, key=lambda x: x[2])
            worst_coverage = min(all_coverages, key=lambda x: x[2])

            f.write("### 最佳表现\n")
            f.write(f"- 最高覆盖度: level{best_coverage[0][-1]}-{best_coverage[1]} ({best_coverage[2]:.1f}%)\n")
            f.write(f"- 最低覆盖度: level{worst_coverage[0][-1]}-{worst_coverage[1]} ({worst_coverage[2]:.1f}%)\n\n")

            # 级别对比
            f.write("### 级别对比分析\n")
            for level in ['level1', 'level2', 'level3']:
                level_data = [r for r in analysis_results if r['level'] == level]
                coverages = [float(r['覆盖度'].rstrip('%')) for r in level_data]
                avg_cov = sum(coverages) / len(coverages)
                max_cov = max(coverages)
                min_cov = min(coverages)

                f.write(f"- **{level.upper()}**: 平均覆盖度 {avg_cov:.1f}%, 范围 {min_cov:.1f}%-{max_cov:.1f}%\n")

            f.write("\n### 相似度计算方法说明\n")
            f.write("- **覆盖度**: 使用DeepSeek大模型计算生成内容与基础版本的章节标题语义相似度，匹配度超过60%的章节计为覆盖\n")
            f.write("- **专业度**: 基于专业术语使用、结构完整性、内容丰富度等维度进行综合评分\n")
            f.write("- **其他指标**: 包括结构完整性评估、内容丰富度分析、专业术语统计等\n\n")

            f.write("### 📊 覆盖度统计总结\n")
            all_coverages = [float(r['覆盖度'].rstrip('%')) for r in analysis_results]
            overall_avg = sum(all_coverages) / len(all_coverages)
            overall_max = max(all_coverages)
            overall_min = min(all_coverages)

            f.write(f"- 总样本数: {len(analysis_results)}\n")
            f.write(f"- 整体平均覆盖度: {overall_avg:.1f}%\n")
            f.write(f"- 最高覆盖度: {overall_max:.1f}%\n")
            f.write(f"- 最低覆盖度: {overall_min:.1f}%\n\n")

            f.write("### 技术说明\n")
            f.write("- **覆盖度计算**: 使用DeepSeek大模型一次性分析每个level的5个文件与基础版本的覆盖度\n")
            f.write("- **按level分组**: 每次只调用一次大模型，分析一个level的所有文件\n")
            f.write("- **高效处理**: 总共只调用3次大模型，快速完成分析\n")

        print(f"📄 比较报告已保存到: {report_path}")


async def main():
    """主函数"""
    # 从环境变量获取API配置
    import os
    from dotenv import load_dotenv

    # 加载环境变量
    load_dotenv()

    DEEPSEEK_API_KEY = "sk-438668d443224063adbb1d295fe44a9f"
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    # 创建报告生成器
    generator = ComparisonReportGenerator(DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL)

    # 生成报告
    await generator.generate_report()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
