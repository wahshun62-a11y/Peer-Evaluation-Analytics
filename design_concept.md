# Network Analyzer Design System

> **Context**: 이 문서는 `@[동료평가/network-analyzer]` 프로젝트의 디자인 컨셉(Color, Tone, Look & Feel)을 정의한 문서입니다. 향후 Vibe Coding 시 모든 시스템에 동일한 디자인 컨셉을 적용하기 위한 Context 지식으로 활용됩니다.

---

## 1. Design Philosophy (디자인 철학)

- **Core Theme**: **"Warm Professionalism"**
- **Concept**: 차가운 데이터 분석 도구의 이미지를 탈피하고, 인사(HR) 도메인 특유의 "사람 중심" 따뜻함을 부여하기 위해 **Warm Beige** 배경과 신뢰감을 주는 **Deep Navy**를 조합했습니다.
- **Keywords**: `Structured`, `Trustworthy`, `Clean`, `Human-Centric`
- **Look & Feel**:
  - **Glassmorphism**: 사이드바와 헤더에 은은한 투명도와 그라디언트를 사용하여 깊이감을 줌.
  - **Soft Shadows**: 강한 그림자 대신 부드러운 확산형 그림자 사용하여 '종이' 위에 정보가 떠 있는 듯한 느낌.
  - **Roundness**: 날카로운 직각 대신 `8px ~ 20px`의 둥근 모서리를 사용하여 부드러운 인상.

---

## 2. Color Palette (색상 시스템)

### 🎨 Primary Colors (브랜드 컬러)
| Role | Color Name | Hex Code | Usage |
|------|------------|----------|-------|
| **Brand Base** | **Deep Navy** | `#002060` | 사이드바, 주요 버튼, 강조 텍스트 |
| **Brand Dark** | Navy 900 | `#001440` | 사이드바 그라디언트 (Deep) |
| **Brand Light** | Navy 400 | `#1A5CC8` | 링크, 활성화 상태, 아이콘 |
| **Background** | **Warm Beige** | `#F0EAE7` | 앱 전체 배경 (Main Background) |
| **Surface** | **White** | `#FFFFFF` | 카드, 패널, 모달 배경 |

### 🚦 Semantic Colors (기능성 컬러)
| Role | Hex Code | Background (Bg) | Usage |
|------|----------|-----------------|-------|
| **Success** | `#0D8050` | `#E6F4EC` | 긍정 지표, 완료, 안전 |
| **Caution** | `#B8860B` | `#FFF8E1` | 주의 필요, 중간 상태 |
| **Warning** | `#C62828` | `#FFEBEE` | 위험, 경고, 부정 지표 |

### 📝 Typography Colors (텍스트)
| Role | Hex Code | Description |
|------|----------|-------------|
| **Primary** | `#1A1A2E` | 본문, 제목 (거의 블랙에 가까운 네이비) |
| **Secondary**| `#4A4A5A` | 부가 설명, 라벨 |
| **Muted** | `#8A8A9A` | 비활성 텍스트, 플레이스홀더 |
| **On Navy** | `#FFFFFF` | 사이드바 내 텍스트 |

---

## 3. Typography (타이포그래피)

- **Font Family**: `'Inter'`, `'Pretendard'`, `-apple-system`, `sans-serif`
- **Line Height**: `1.6` (가독성을 위한 넉넉한 줄간격)

### Scale & Weight
| Usage | Size (rem) | Pixel (approx) | Weight |
|-------|------------|----------------|--------|
| **Display** | `2.0rem` (3xl) | 32px | 800 (ExtraBold) |
| **H1** | `1.6rem` (2xl) | 25.6px | 700 (Bold) |
| **H2** | `1.35rem` (xl)| 21.6px | 700 (Bold) |
| **H3** | `1.1rem` (lg) | 17.6px | 600 (SemiBold) |
| **Body** | `0.95rem` (base)| 15.2px | 400 (Regular) |
| **Small** | `0.8rem` (sm) | 12.8px | 500 (Medium) |
| **Tiny** | `0.7rem` (xs) | 11.2px | 600 (SemiBold) |

---

## 4. UI Components & Elements (컴포넌트 스타일)

### 🗂️ Cards (카드)
- **Background**: White `#FFFFFF`
- **Border**: `1px solid rgba(0, 32, 96, 0.08)`
- **Radius**: `14px` (Large)
- **Shadow**: `0 2px 8px rgba(0, 32, 96, 0.06)` (Soft)
- **Interaction**: Hover 시 `transform: translateY(-2px)` 및 Shadow 심화.
- **Top Accent**: 카드 상단에 `3px` 컬러 라인(성공/주의/경고) 적용 가능.

### 🔘 Buttons (버튼)
- **Primary**:
  - Background: `linear-gradient(135deg, #FFFFFF 0%, #F0EAE7 100%)` (미세한 그라디언트)
  - Text: Navy `#002060`
  - Shadow: `0 2px 8px rgba(0, 0, 0, 0.15)`
- **Secondary**:
  - Background: `rgba(255, 255, 255, 0.08)` (Glass)
  - Border: `1px solid rgba(255, 255, 255, 0.12)`
  - Text: White (Opacity 0.7)

### 🧊 Filter Chips (필터 칩 - 사이드바)
- **Default**: `rgba(255, 255, 255, 0.06)` 배경, 투명도 있는 텍스트.
- **Active**: `rgba(255, 255, 255, 0.95)` (거의 흰색), Navy 텍스트, `font-weight: 600`.
- **Shape**: `border-radius: 20px` (Fully Rounded).

### 📑 Tabs (탭 네비게이션)
- **Style**: 텍스트 중심, 배경 없음.
- **Active**: 하단 `2px` Border (`#002D80`), 글자색 진하게.
- **Hover**: 배경색 미세하게 추가 (`#E3EFF9`), 상단 모서리 둥글게.

---

## 5. Data Visualization (데이터 시각화)

### 🕸️ Network Graph (Nodes & Edges)
- **Nodes**:
  - Size: 연결 정도(Degree)에 비례 (`10 + Math.sqrt(deg) * 3`).
  - Ghost Node (외부 인원): `borderDashes: [4, 4]`, Opacity `0.6`, Grayscale.
- **Edges**:
  - Style: `curvedCW` (부드러운 곡선), `roundness: 0.1`.
  - Arrow: `scaleFactor: 0.4` (작고 세련된 화살표).

### 📈 Sparklines (미니 차트)
- **Line Color**: Navy (`#002D80`).
- **Style**: `stroke-width: 1.5`, `fill: none`.
- **Dots**: 데이터 포인트에 마우스 오버 시 원형 툴팁 표시.

### 📊 Progress / Distribution Bars
- **Team**: Green (`#4ade80`)
- **Dept**: Amber (`#fbbf24`)
- **Cross**: Red (`#f87171`)
- **Style**: 얇은 바 형태, 둥근 모서리 없음(Stack 형태).

---

## 6. Layout & Spacing (레이아웃 규칠)

### 📏 Spacing System
- 기본 단위: `4px`
- `--space-1`: 4px
- `--space-2`: 8px
- `--space-3`: 12px
- `--space-4`: 16px
- `--space-5`: 20px
- `--space-6`: 24px
- `--space-8`: 32px (Section Padding)
- `--space-12`: 48px (Large Padding)

### 📐 Dimensions
- **Sidebar Width**: `300px` (Fixed)
- **Header Height**: `56px`
- **Tab Height**: `48px`

### ✨ Animation & Transitions
- **Hover**: `0.15s ease` (빠릿한 반응)
- **Layout Change**: `0.25s ease` (부드러운 전환)
- **Keyframes**:
  - `fadeIn`: 아래에서 위로 투명도 변화.
  - `float-gentle`: 플레이스홀더 아이콘 둥둥 떠있는 효과.
  - `pulse-dot`: 상태 표시 점 깜빡임.

---

## 7. CSS Implementation (Variables)
```css
:root {
    /* Primary Palette */
    --color-bg: #F0EAE7;
    --color-bg-card: #FFFFFF;
    --color-bg-sidebar: #002060;

    /* Semantic */
    --color-success: #0D8050;
    --color-caution: #B8860B;
    --color-warning: #C62828;

    /* Typo */
    --font-family: 'Inter', 'Pretendard', sans-serif;
    --color-text-primary: #1A1A2E;
    --color-text-muted: #8A8A9A;

    /* Shadows */
    --shadow-sm: 0 1px 3px rgba(0, 32, 96, 0.06);
    --shadow-card: 0 2px 8px rgba(0, 32, 96, 0.06), 0 0 0 1px rgba(0, 32, 96, 0.04);

    /* Spacing & Radius */
    --radius-md: 10px;
    --radius-lg: 14px;
}
```
