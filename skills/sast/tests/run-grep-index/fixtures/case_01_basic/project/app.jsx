function render(el, userInput) {
  el.innerHTML = userInput;
}

function danger() {
  return <div dangerouslySetInnerHTML={{__html: data}} />;
}
