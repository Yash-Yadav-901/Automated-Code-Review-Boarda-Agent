import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

def generate_diagram(output_path: str = "architecture_diagram.png"):
    fig, ax = plt.subplots(figsize=(14, 10), dpi=300)
    ax.set_facecolor("#0F172A")
    fig.patch.set_facecolor("#0F172A")

    # Title
    ax.text(7, 9.5, "AUTOMATED CODE REVIEW BOARD (MULTI-AGENT ARCHITECTURE)", 
            color="#38BDF8", fontsize=16, fontweight="bold", ha="center")
    ax.text(7, 9.15, "Coordination: Fan-Out / Fan-In with Reviewer Manager & Group-of-3 Patch Agent | Framework: Semantic Kernel", 
            color="#94A3B8", fontsize=11, ha="center")

    # Box styling helper
    def draw_box(x, y, w, h, title, subtitle, color, text_color="white", edge_color="#38BDF8"):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2",
                                      facecolor=color, edgecolor=edge_color, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h*0.65, title, color=text_color, fontsize=11, fontweight="bold", ha="center", va="center")
        ax.text(x + w/2, y + h*0.32, subtitle, color="#E2E8F0", fontsize=8.5, ha="center", va="center")

    # 1. Input Diff
    draw_box(0.5, 7.2, 3.0, 1.2, "Raw Git Diff / PR", "Unified patch stream\nAdded / Deleted Lines", "#1E293B", edge_color="#64748B")

    # 2. Diff Agent
    draw_box(4.5, 7.2, 3.2, 1.2, "Diff Agent (Module 1)", "Tools: parse_unified_diff\ncompute_diff_metrics", "#1E3A8A", edge_color="#60A5FA")

    # 3. Shared State
    draw_box(9.0, 7.0, 4.2, 1.6, "Shared ChangeState", "Files • Hunks • AST Metrics\nAppend-only Findings List\nExecution Trace Records", "#312E81", edge_color="#A78BFA")

    # 4. Fan-Out Parallel Review Specialists
    draw_box(0.6, 4.4, 3.6, 1.3, "Style Agent (Module 2)", "Tools: check_pep8_and_docstrings\ncalculate_cyclomatic_complexity", "#14532D", edge_color="#4ADE80")
    draw_box(5.2, 4.4, 3.6, 1.3, "Security Agent (Module 3)", "Tools: scan_secrets_and_credentials\naudit_code_vulnerabilities", "#7F1D1D", edge_color="#F87171")
    draw_box(9.8, 4.4, 3.6, 1.3, "Test-Coverage Agent (Mod 4)", "Tools: detect_test_file_presence\nevaluate_test_adequacy", "#78350F", edge_color="#FBBF24")

    # 5. Fan-In Reviewer Manager
    draw_box(4.5, 2.2, 5.0, 1.4, "Reviewer Manager (Module 5)", "Tools: deduplicate_and_rank_findings\ncompute_merge_verdict\nVerdict: APPROVE vs REQUEST-CHANGES", "#1E293B", edge_color="#38BDF8")

    # 6. Group-of-3 Add-On: Fix Suggestion Agent
    draw_box(0.5, 0.4, 5.0, 1.3, "Fix-Suggestion Agent (Module 6)", "Tools: extract_code_context\ngenerate_unified_patch\n[Group-of-3 Add-on]", "#581C87", edge_color="#C084FC")

    # 7. Audit Run Log
    draw_box(7.5, 0.4, 5.5, 1.3, "Append-Only Audit Log", "File: audit_run_log.jsonl\nJSONL Trail: Timestamps, Tools, Outputs", "#0F172A", edge_color="#94A3B8")

    # Arrows
    arrow_props = dict(arrowstyle="->", color="#38BDF8", lw=2, mutation_scale=15)
    purple_props = dict(arrowstyle="->", color="#A78BFA", lw=2, mutation_scale=15)
    green_props = dict(arrowstyle="->", color="#4ADE80", lw=2, mutation_scale=15)
    red_props = dict(arrowstyle="->", color="#F87171", lw=2, mutation_scale=15)

    # Input -> Diff Agent -> Shared State
    ax.annotate("", xy=(4.5, 7.8), xytext=(3.5, 7.8), arrowprops=arrow_props)
    ax.annotate("", xy=(9.0, 7.8), xytext=(7.7, 7.8), arrowprops=arrow_props)

    # Shared State -> Fan-out to 3 Agents
    ax.annotate("", xy=(2.4, 5.7), xytext=(10.0, 7.0), arrowprops=purple_props)
    ax.annotate("", xy=(7.0, 5.7), xytext=(11.0, 7.0), arrowprops=purple_props)
    ax.annotate("", xy=(11.6, 5.7), xytext=(12.0, 7.0), arrowprops=purple_props)

    # 3 Agents -> Fan-in back to Reviewer Manager
    ax.annotate("", xy=(5.5, 3.6), xytext=(2.4, 4.4), arrowprops=green_props)
    ax.annotate("", xy=(7.0, 3.6), xytext=(7.0, 4.4), arrowprops=red_props)
    ax.annotate("", xy=(8.5, 3.6), xytext=(11.6, 4.4), arrowprops=arrow_props)

    # Reviewer Manager -> Fix-Suggestion Agent & Audit Log
    ax.annotate("", xy=(3.0, 1.7), xytext=(5.5, 2.2), arrowprops=purple_props)
    ax.annotate("", xy=(10.0, 1.7), xytext=(8.5, 2.2), arrowprops=arrow_props)

    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10.2)
    ax.axis("off")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    print(f"Architecture diagram saved to {output_path}")

if __name__ == "__main__":
    generate_diagram()
