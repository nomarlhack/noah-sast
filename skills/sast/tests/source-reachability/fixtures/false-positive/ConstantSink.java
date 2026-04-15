package fixture;

import java.io.PrintWriter;

// xss-scanner Sink 패턴에 걸리지만 인자가 컴파일 타임 상수.
// 기대: Phase 1에서 후보 등록 안 됨 (guidelines-phase1.md §8 Source 도달성 실패).
// Phase 1이 잘못 등록하면 scan-report-review checklist §9 / §4-1(e)가 재분류.
public class ConstantSink {
    private static final String BANNER = "<b>Welcome</b>";

    public void render(PrintWriter out) {
        String banner = BANNER;
        out.print(banner);
    }

    public void renderLiteral(PrintWriter out) {
        out.print("<h1>Static Title</h1>");
    }

    public void renderInternalId(PrintWriter out) {
        String id = java.util.UUID.randomUUID().toString();
        out.print(id);
    }
}
