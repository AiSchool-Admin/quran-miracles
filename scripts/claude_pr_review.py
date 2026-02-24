"""Claude Code PR review script — used by GitHub Actions."""

import anthropic
import argparse
import subprocess


def review_pr(diff_file: str, pr_number: int, repo: str, guidelines_file: str):
    with open(diff_file, "r") as f:
        diff = f.read()

    with open(guidelines_file, "r") as f:
        guidelines = f.read()

    client = anthropic.Anthropic()

    review = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=3000,
        system=f"""أنت مراجع كود متخصص في مشروع "معجزات القرآن الكريم".

قواعد المشروع المُلزِمة:
{guidelines[:3000]}

مهمتك: مراجعة التغييرات والتحقق من:
1. الالتزام بقواعد المشروع (CLAUDE.md)
2. جودة الكود وأفضل الممارسات
3. الأمانة العلمية في أي ادعاءات قرآنية
4. صحة نظام المستويات (tier_0 → tier_4)
5. وجود dir=rtl في كل مكوّن frontend جديد
6. عدم تعديل النص القرآني

اكتب ملاحظاتك بالعربية مع أمثلة محددة من الكود.""",
        messages=[
            {
                "role": "user",
                "content": f"راجع هذه التغييرات:\n\n```diff\n{diff[:8000]}\n```",
            }
        ],
    )

    review_text = review.content[0].text
    comment = f"## مراجعة Claude Code\n\n{review_text}"

    subprocess.run(
        [
            "gh",
            "pr",
            "comment",
            str(pr_number),
            "--repo",
            repo,
            "--body",
            comment,
        ],
        check=True,
    )

    print(f"Review posted on PR #{pr_number}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--diff-file")
    parser.add_argument("--pr-number", type=int)
    parser.add_argument("--repo")
    parser.add_argument("--guidelines-file")
    args = parser.parse_args()

    review_pr(args.diff_file, args.pr_number, args.repo, args.guidelines_file)
