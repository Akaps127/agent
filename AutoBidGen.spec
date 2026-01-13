# -*- mode: python ; coding: utf-8 -*-
"""
AutoBidGen PyInstaller Spec File
백엔드 + 프론트엔드 통합 exe 빌드 설정
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 기본 경로
BASE_PATH = os.path.dirname(os.path.abspath(SPEC))

# 숨겨진 imports (동적으로 로드되는 모듈들)
hidden_imports = [
    # LangChain 관련
    'langchain',
    'langchain_core',
    'langchain_openai',
    'langchain_anthropic',
    'langchain_google_genai',
    'langgraph',
    
    # FastAPI/Uvicorn 관련
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'fastapi',
    'starlette',
    'pydantic',
    
    # 데이터 처리
    'pandas',
    'openpyxl',
    'pypdf',
    'pdfplumber',
    'python-docx',
    'docx',
    
    # 기타
    'dotenv',
    'httpx',
    'httpcore',
    'anyio',
    'sniffio',
    'h11',
    'certifi',
    'charset_normalizer',
    'idna',
    'urllib3',
    'olefile',
    'holidayskr',
    
    # 프로젝트 모듈
    'src',
    'src.parser',
    'src.config',
    'src.schema',
    'src.parameters',
    'src.graph',
    'src.g2b_api',
    'src.g2b_api_wrapper',
    'src.industry_api',
    'src.product_mapping',
    'src.nodes',
    'src.nodes.planner',
    'src.nodes.writer',
    'src.nodes.docx_writer',
    'src.services',
    'src.services.verification_service',
    'src.utils',
]

# 데이터 파일 수집
datas = [
    # 프론트엔드 정적 파일
    (os.path.join(BASE_PATH, 'frontend', 'out'), 'frontend_static'),
    
    # 참조 데이터
    (os.path.join(BASE_PATH, 'reference_data'), 'reference_data'),
    
    # src 모듈 (템플릿 등 포함)
    (os.path.join(BASE_PATH, 'src'), 'src'),
]

# Analysis
a = Analysis(
    [os.path.join(BASE_PATH, 'app_standalone.py')],
    pathex=[BASE_PATH],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'PIL',
        'scipy',
        'numpy.tests',
        'pandas.tests',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AutoBidGen',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 콘솔 창 표시 (디버깅용)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 아이콘 파일이 있으면 여기에 경로 지정
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AutoBidGen',
)
