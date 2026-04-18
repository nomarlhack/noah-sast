function runEval(code) {
  return eval(code);
}

const template = `hello ${name}`;

const safe_html = "<%= user.input | safe %>";
