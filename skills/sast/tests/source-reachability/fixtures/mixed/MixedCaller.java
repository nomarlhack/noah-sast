package fixture;

import javax.servlet.http.HttpServletRequest;
import java.io.PrintWriter;

// 한 Sink 함수(write)가 두 호출 경로를 가진다.
// - handleUser: Source 도달 (getParameter)       → 후보 유지
// - handleStatic: 상수                            → 폐기
// 기대: _principles.md §1 Source 도달성 판정의 혼합 케이스 규칙에 따라 Source 도달 경로만 후보로 유지.
public class MixedCaller {
    public void write(PrintWriter out, String value) {
        out.print(value);
    }

    public void handleUser(HttpServletRequest request, PrintWriter out) {
        String q = request.getParameter("q");
        write(out, q);
    }

    public void handleStatic(PrintWriter out) {
        write(out, "<b>Fixed banner</b>");
    }
}
