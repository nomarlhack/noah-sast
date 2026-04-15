package fixture;

import javax.servlet.http.HttpServletRequest;
import java.io.PrintWriter;

// 진성 XSS 케이스. getParameter Source → out.print Sink.
// 기대: Phase 1에서 후보 등록, scan-report-review도 유지.
public class UserInputSink {
    public void handle(HttpServletRequest request, PrintWriter out) {
        String q = request.getParameter("q");
        out.print(q);
    }
}
