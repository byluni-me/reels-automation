"""Gradio UI 레이아웃 + 이벤트 바인딩"""
import gradio as gr

from reels.gui.constants import VOICE_CHOICES, RATE_CHOICES, SCRIPT_TEMPLATE, CAPTION_TEMPLATE
from reels.gui.handlers import (
    get_status_summary,
    load_ideas_table,
    handle_import_csv,
    handle_add_idea,
    handle_next_id,
    handle_import_scripts_file,
    handle_import_scripts_text,
    handle_generate_voices,
    handle_generate_videos,
    handle_import_captions_file,
    handle_import_captions_text,
    handle_publish,
    handle_mark_published,
)


def build_app() -> gr.Blocks:
    with gr.Blocks(
        title="Reels 자동화",
        theme=gr.themes.Soft(primary_hue="red", secondary_hue="blue"),
        css="""
        .status-box textarea { font-family: monospace !important; font-size: 13px !important; }
        .log-box textarea { font-family: monospace !important; font-size: 12px !important; }
        """,
    ) as app:

        gr.Markdown("# Instagram Reels 자동화 파이프라인")
        gr.Markdown("수동 입력 + edge-tts(무료) + ffmpeg + Pexels(무료) 기반")

        # ─── 대시보드 ─────────────────────────────────────
        with gr.Tab("대시보드"):
            status_box = gr.Textbox(
                label="현황",
                value=get_status_summary(),
                lines=20,
                interactive=False,
                elem_classes="status-box",
            )
            refresh_btn = gr.Button("새로고침", variant="secondary")
            refresh_btn.click(fn=get_status_summary, outputs=status_box)

            gr.Markdown("### 전체 아이디어 목록")
            ideas_table = gr.Dataframe(
                headers=["ID", "제목", "주제", "각도", "Hook", "상태", "생성일"],
                value=load_ideas_table(),
                interactive=False,
                wrap=True,
            )
            refresh_table_btn = gr.Button("목록 새로고침", variant="secondary")
            refresh_table_btn.click(fn=load_ideas_table, outputs=ideas_table)

        # ─── 1단계: 아이디어 ──────────────────────────────
        with gr.Tab("1. 아이디어"):
            gr.Markdown("### CSV 파일 업로드")
            gr.Markdown("필수 컬럼: `id, title, topic, angle, hook`")
            with gr.Row():
                csv_file = gr.File(label="CSV 파일", file_types=[".csv"])
                csv_upload_btn = gr.Button("CSV 등록", variant="primary")
            csv_result = gr.Textbox(label="결과", lines=5, interactive=False, elem_classes="log-box")
            csv_table = gr.Dataframe(
                headers=["ID", "제목", "주제", "각도", "Hook", "상태", "생성일"],
                value=load_ideas_table(),
                interactive=False,
                wrap=True,
            )
            csv_upload_btn.click(
                fn=handle_import_csv,
                inputs=[csv_file],
                outputs=[csv_result, csv_table],
            )

            gr.Markdown("---")
            gr.Markdown("### 수동 입력 (1개씩)")
            with gr.Row():
                idea_id = gr.Number(label="ID", value=handle_next_id(), precision=0)
                idea_title = gr.Textbox(label="제목", placeholder="전세의 함정")
            with gr.Row():
                idea_topic = gr.Textbox(label="주제", placeholder="부동산 공부")
                idea_angle = gr.Textbox(label="각도", placeholder="전세 보증금 반환 리스크")
            idea_hook = gr.Textbox(label="Hook", placeholder="전세가 무조건 이득이라고?")
            add_idea_btn = gr.Button("아이디어 추가", variant="primary")
            add_result = gr.Textbox(label="결과", lines=2, interactive=False)

            add_idea_btn.click(
                fn=handle_add_idea,
                inputs=[idea_id, idea_title, idea_topic, idea_angle, idea_hook],
                outputs=[add_result, csv_table],
            ).then(fn=handle_next_id, outputs=idea_id)

        # ─── 2단계: 스크립트 ──────────────────────────────
        with gr.Tab("2. 스크립트"):
            gr.Markdown("### JSON 파일 업로드")
            with gr.Row():
                script_file = gr.File(label="스크립트 JSON", file_types=[".json"])
                script_upload_btn = gr.Button("JSON 등록", variant="primary")
            script_file_result = gr.Textbox(label="결과", lines=5, interactive=False, elem_classes="log-box")
            script_upload_btn.click(
                fn=handle_import_scripts_file,
                inputs=[script_file],
                outputs=[script_file_result],
            )

            gr.Markdown("---")
            gr.Markdown("### 직접 JSON 입력")
            script_text = gr.Code(
                label="스크립트 JSON",
                value=SCRIPT_TEMPLATE,
                language="json",
                lines=25,
            )
            script_text_btn = gr.Button("JSON 등록", variant="primary")
            script_text_result = gr.Textbox(label="결과", lines=5, interactive=False, elem_classes="log-box")
            script_text_btn.click(
                fn=handle_import_scripts_text,
                inputs=[script_text],
                outputs=[script_text_result],
            )

        # ─── 3단계: 음성 ─────────────────────────────────
        with gr.Tab("3. 음성 (edge-tts)"):
            gr.Markdown("### 음성 생성 설정")
            gr.Markdown("scripted 상태의 스크립트에 대해 음성을 생성합니다. (무료)")

            with gr.Row():
                voice_select = gr.Dropdown(
                    label="음성 선택",
                    choices=VOICE_CHOICES,
                    value=VOICE_CHOICES[0],
                )
                rate_select = gr.Dropdown(
                    label="속도",
                    choices=RATE_CHOICES,
                    value=RATE_CHOICES[3],
                )
                voice_limit = gr.Number(label="처리 수 제한 (0=전체)", value=0, precision=0)

            voice_btn = gr.Button("음성 생성 시작", variant="primary", size="lg")
            voice_log = gr.Textbox(label="로그", lines=15, interactive=False, elem_classes="log-box")

            gr.Markdown("### 생성된 음성 미리듣기")
            voice_audio_list = gr.File(label="음성 파일", file_count="multiple", interactive=False)

            voice_btn.click(
                fn=handle_generate_voices,
                inputs=[voice_select, rate_select, voice_limit],
                outputs=[voice_log, voice_audio_list],
            )

        # ─── 4단계: 영상 ─────────────────────────────────
        with gr.Tab("4. 영상 (ffmpeg)"):
            gr.Markdown("### 영상 생성 설정")
            gr.Markdown("voiced 상태의 아이디어에 대해 영상을 생성합니다.")

            with gr.Row():
                pexels_check = gr.Checkbox(label="Pexels 스톡 영상 배경 사용 (무료)", value=False)
                pexels_query_input = gr.Textbox(
                    label="Pexels 검색어 (비우면 자동 추출)",
                    placeholder="money finance",
                )
                video_limit = gr.Number(label="처리 수 제한 (0=전체)", value=0, precision=0)

            video_btn = gr.Button("영상 생성 시작", variant="primary", size="lg")
            video_log = gr.Textbox(label="로그", lines=15, interactive=False, elem_classes="log-box")

            gr.Markdown("### 생성된 영상")
            video_file_list = gr.File(label="영상 파일", file_count="multiple", interactive=False)

            video_btn.click(
                fn=handle_generate_videos,
                inputs=[pexels_check, pexels_query_input, video_limit],
                outputs=[video_log, video_file_list],
            )

        # ─── 5단계: 캡션 ─────────────────────────────────
        with gr.Tab("5. 캡션"):
            gr.Markdown("### JSON 파일 업로드")
            with gr.Row():
                caption_file = gr.File(label="캡션 JSON", file_types=[".json"])
                caption_upload_btn = gr.Button("JSON 등록", variant="primary")
            caption_file_result = gr.Textbox(label="결과", lines=5, interactive=False, elem_classes="log-box")
            caption_upload_btn.click(
                fn=handle_import_captions_file,
                inputs=[caption_file],
                outputs=[caption_file_result],
            )

            gr.Markdown("---")
            gr.Markdown("### 직접 JSON 입력")
            caption_text = gr.Code(
                label="캡션 JSON",
                value=CAPTION_TEMPLATE,
                language="json",
                lines=25,
            )
            caption_text_btn = gr.Button("JSON 등록", variant="primary")
            caption_text_result = gr.Textbox(label="결과", lines=5, interactive=False, elem_classes="log-box")
            caption_text_btn.click(
                fn=handle_import_captions_text,
                inputs=[caption_text],
                outputs=[caption_text_result],
            )

        # ─── 6단계: Publish ──────────────────────────────
        with gr.Tab("6. Publish"):
            gr.Markdown("### rendered -> publish/ 정리")
            gr.Markdown("영상 + 캡션 + 썸네일을 publish 폴더로 정리합니다.")
            with gr.Row():
                publish_limit = gr.Number(label="처리 수 제한 (0=전체)", value=0, precision=0)
                publish_btn = gr.Button("Publish 정리 실행", variant="primary")
            publish_log = gr.Textbox(label="로그", lines=10, interactive=False, elem_classes="log-box")

            gr.Markdown("---")
            gr.Markdown("### 게시 완료 처리")
            with gr.Row():
                published_ids = gr.Textbox(
                    label="Published로 변경할 ID (공백 구분)",
                    placeholder="1 2 3",
                )
                mark_btn = gr.Button("Published 처리", variant="secondary")
            mark_result = gr.Textbox(label="결과", lines=3, interactive=False)

            publish_status = gr.Textbox(
                label="현황",
                value=get_status_summary(),
                lines=15,
                interactive=False,
                elem_classes="status-box",
            )

            publish_btn.click(
                fn=handle_publish,
                inputs=[publish_limit],
                outputs=[publish_log, publish_status],
            )
            mark_btn.click(
                fn=handle_mark_published,
                inputs=[published_ids],
                outputs=[mark_result, publish_status],
            )

    return app
