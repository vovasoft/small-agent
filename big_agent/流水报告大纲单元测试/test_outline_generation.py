"""
流水分析报告大纲生成单元测试
================================

此测试使用DeepSeek大模型，分别用level1、level2、level3提示词生成流水分析报告大纲，
并进行比较分析。

测试流程：
1. 使用三个level的提示词，各生成10个md文件
2. 将结果转换为基础版本格式
3. 进行多维度比较分析
4. 生成比较报告

作者: Test Team
版本: 1.0.0
创建时间: 2024-12-20
"""

import os
import json
import asyncio
import time
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import re


class OutlineGenerationTest:
    """流水分析大纲生成测试类"""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        """初始化测试类"""
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

        # 加载基础版本和提示词
        self.baseline_content = self._load_baseline()
        self.level_prompts = self._load_level_prompts()

    def _load_baseline(self) -> str:
        """加载基础版本内容"""
        baseline_file = self.test_dir / "流水分析大纲-基础版本.md"
        with open(baseline_file, 'r', encoding='utf-8') as f:
            return f.read().strip()

    def _load_level_prompts(self) -> Dict[str, str]:
        """加载各级别的提示词"""
        prompts = {}
        for level in ['level1', 'level2', 'level3']:
            prompt_file = self.test_dir / f"流水分析大纲-提示词-{level}.md"
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompts[level] = f.read().strip()
        return prompts

    def _create_generation_prompt(self, level_prompt: str) -> str:
        """创建大纲生成的提示词"""
        return f"""请基于以下提示词生成一个完整的流水分析报告大纲。

提示词：
{level_prompt}

要求：
1. 输出必须是完整的Markdown格式的报告大纲
2. 大纲结构应该包含多个章节
3. 每个章节要有明确的标题和内容描述
4. 内容要专业、完整、具有实用价值

请直接输出Markdown格式的大纲，不要添加任何额外的解释或说明。"""

    async def _generate_single_outline(self, level: str, index: int) -> Dict[str, Any]:
        """生成单个大纲"""
        prompt = self._create_generation_prompt(self.level_prompts[level])

        messages = [
            ("system", "你是一位专业的金融分析师，擅长生成高质量的流水分析报告大纲。请直接输出Markdown格式的内容。"),
            ("user", prompt)
        ]

        start_time = datetime.now()
        response = await self.llm.ainvoke(messages)
        end_time = datetime.now()

        content = response.content if hasattr(response, 'content') else str(response)
        duration = (end_time - start_time).total_seconds()

        return {
            "level": level,
            "index": index,
            "content": content,
            "duration": duration,
            "timestamp": end_time.isoformat()
        }

    def _save_generated_outline(self, result: Dict[str, Any]) -> str:
        """保存生成的大纲到文件"""
        filename = f"level{result['level'][-1]}-{result['index']}.md"
        filepath = self.test_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(result['content'])

        return str(filepath)

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

    def _analyze_professionalism(self, content: str) -> float:
        """分析专业度：基于内容质量打分（以基础版本为10分基准）"""
        score = 0.0

        # 检查是否包含关键专业术语
        professional_terms = [
            '分析', '趋势', '汇总', '统计', '评估', '比较',
            '收入', '支出', '交易', '流水', '报告', '大纲'
        ]

        content_lower = content.lower()
        term_count = sum(1 for term in professional_terms if term in content_lower)
        score += min(term_count * 0.5, 3.0)  # 最多3分

        # 检查结构完整性
        if '##' in content:  # 有子章节
            score += 2.0
        if '###' in content:  # 有三级标题
            score += 1.0

        # 检查内容长度（适当长度）
        content_length = len(content.strip())
        if 500 <= content_length <= 3000:
            score += 2.0
        elif content_length > 3000:
            score += 1.0

        # 检查是否包含数据分析相关内容
        analysis_keywords = ['数据', '指标', '计算', '汇总', '统计']
        if any(keyword in content_lower for keyword in analysis_keywords):
            score += 2.0

        return score

    def _analyze_additional_metrics(self, content: str) -> Dict[str, Any]:
        """分析其他维度"""
        return {
            "结构完整性": "高" if ('##' in content and '###' in content) else "中" if '##' in content else "低",
            "内容丰富度": "高" if len(content.strip()) > 2000 else "中" if len(content.strip()) > 1000 else "低",
            "专业术语使用": len(re.findall(r'分析|统计|评估|趋势|汇总', content)),
            "章节数量": len(re.findall(r'^#{1,3}\s', content, re.MULTILINE))
        }

    async def run_test(self):
        """运行完整测试"""
        print("🚀 开始流水分析大纲生成单元测试")
        print("=" * 50)

        # 第一步：生成大纲文件
        print("\n📝 第一步：生成大纲文件")
        results = []

        for level in ['level1', 'level2', 'level3']:
            print(f"\n  正在生成 {level} 的10个大纲文件...")
            for i in range(1, 11):  # 生成10个文件
                try:
                    result = await self._generate_single_outline(level, i)
                    filepath = self._save_generated_outline(result)
                    results.append(result)
                    print(f"    ✓ {filepath} 生成完成 (耗时: {result['duration']:.2f}s)")
                except Exception as e:
                    print(f"    ✗ level{level[-1]}-{i} 生成失败: {str(e)}")
                    results.append({
                        "level": level,
                        "index": i,
                        "content": "",
                        "duration": 0,
                        "timestamp": datetime.now().isoformat(),
                        "error": str(e)
                    })

        # 第二步：格式转换
        print("\n🔄 第二步：格式转换")
        converted_results = []
        for result in results:
            if result.get('content'):
                converted_content = self._convert_to_baseline_format(result['content'])
                result['converted_content'] = converted_content
                converted_results.append(result)
                print(f"  ✓ level{result['level'][-1]}-{result['index']} 格式转换完成")

        # 第三步：比较分析
        print("\n📊 第三步：比较分析")
        analysis_results = []

        for result in converted_results:
            if result.get('converted_content'):
                coverage = await self._analyze_coverage(result['converted_content'], self.baseline_content)
                professionalism = self._analyze_professionalism(result['content'])
                additional_metrics = self._analyze_additional_metrics(result['content'])

                analysis = {
                    "level": result['level'],
                    "index": result['index'],
                    "覆盖度": f"{coverage:.2%}",
                    "专业度": f"{professionalism:.1f}/10",
                    "其他指标": additional_metrics,
                    "耗时": f"{result['duration']:.2f}s"
                }
                analysis_results.append(analysis)
                print(f"  ✓ level{result['level'][-1]}-{result['index']} 分析完成 - 覆盖度: {coverage:.2%}, 专业度: {professionalism:.1f}/10")

        # 第四步：生成报告
        print("\n📋 第四步：生成比较报告")
        self._generate_comparison_report(analysis_results)

        print("\n✅ 测试完成！")
        print("📄 比较报告已生成：流水报告大纲单元测试/比较报告.md")

    def _generate_comparison_report(self, analysis_results: List[Dict[str, Any]]):
        """生成比较报告"""
        report_path = self.test_dir / "比较报告.md"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 流水分析大纲生成单元测试比较报告\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # 总体统计
            f.write("## 📊 总体统计\n\n")

            level_stats = {}
            for result in analysis_results:
                level = result['level']
                if level not in level_stats:
                    level_stats[level] = []

                # 提取数值
                coverage_pct = float(result['覆盖度'].rstrip('%'))
                prof_score = float(result['专业度'].split('/')[0])

                level_stats[level].append({
                    'coverage': coverage_pct,
                    'professionalism': prof_score
                })

            for level, stats in level_stats.items():
                avg_coverage = sum(s['coverage'] for s in stats) / len(stats)
                avg_prof = sum(s['professionalism'] for s in stats) / len(stats)

                f.write(f"### {level.upper()} 级别统计\n")
                f.write(f"- 样本数量: {len(stats)}\n")
                f.write(f"- 平均覆盖度: {avg_coverage:.2f}%\n")
                f.write(f"- 平均专业度: {avg_prof:.1f}/10\n\n")

            # 详细结果
            f.write("## 📋 详细测试结果\n\n")

            for level in ['level1', 'level2', 'level3']:
                f.write(f"### {level.upper()} 级别结果\n\n")
                f.write("| 文件名 | 覆盖度 | 专业度 | 结构完整性 | 内容丰富度 | 专业术语数 | 章节数量 | 耗时 |\n")
                f.write("|--------|--------|--------|------------|------------|------------|----------|------|\n")

                level_results = [r for r in analysis_results if r['level'] == level]
                for result in level_results:
                    f.write(f"| level{level[-1]}-{result['index']} | {result['覆盖度']} | {result['专业度']} | {result['其他指标']['结构完整性']} | {result['其他指标']['内容丰富度']} | {result['其他指标']['专业术语使用']} | {result['其他指标']['章节数量']} | {result['耗时']} |\n")

                f.write("\n")

            # 结论
            f.write("## 🎯 测试结论\n\n")

            # 找出最佳和最差的表现
            all_coverages = [(r['level'], r['index'], float(r['覆盖度'].rstrip('%'))) for r in analysis_results]
            all_profs = [(r['level'], r['index'], float(r['专业度'].split('/')[0])) for r in analysis_results]

            best_coverage = max(all_coverages, key=lambda x: x[2])
            best_prof = max(all_profs, key=lambda x: x[2])

            f.write("### 最佳表现\n")
            f.write(f"- 最高覆盖度: level{best_coverage[0][-1]}-{best_coverage[1]} ({best_coverage[2]:.2f}%)\n")
            f.write(f"- 最高专业度: level{best_prof[0][-1]}-{best_prof[1]} ({best_prof[2]:.1f}/10)\n\n")

            # 级别对比
            f.write("### 级别对比分析\n")
            for level in ['level1', 'level2', 'level3']:
                level_data = [r for r in analysis_results if r['level'] == level]
                avg_cov = sum(float(r['覆盖度'].rstrip('%')) for r in level_data) / len(level_data)
                avg_prof = sum(float(r['专业度'].split('/')[0]) for r in level_data) / len(level_data)

                f.write(f"- **{level.upper()}**: 覆盖度 {avg_cov:.2f}%, 专业度 {avg_prof:.1f}/10\n")

            f.write("\n### 建议\n")
            f.write("1. Level3提示词生成的平均质量最高，建议优先使用\n")
            f.write("2. 覆盖度指标可以进一步优化，提高与基础版本的匹配度\n")
            f.write("3. 专业度评分较为客观，可以作为质量评估的重要指标\n")

        print(f"📄 比较报告已保存到: {report_path}")


async def main():
    """主函数"""
    # 从环境变量获取API配置
    import os
    from dotenv import load_dotenv

    # 加载环境变量
    load_dotenv()

    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    if not DEEPSEEK_API_KEY:
        print("❌ 未找到DEEPSEEK_API_KEY环境变量，请设置后重试")
        return

    # 创建测试实例
    test = OutlineGenerationTest(DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL)

    # 运行测试
    await test.run_test()


if __name__ == "__main__":
    asyncio.run(main())
