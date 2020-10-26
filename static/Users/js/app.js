function myfunc() {
    var lang = document.getElementById('lang').value;
    if (lang === 'python') this.editor.setOption('mode', 'python');
    else this.editor.setOption('mode', 'clike');
}

var editor = CodeMirror(document.querySelector('.editor-wrapper'), {
    lineNumbers: true,
    tabSize: 2,
    mode: 'clike',
    theme: 'base16-dark',
    styleActiveLine: true,
    autoCloseBrackets: true,
    matchBrackets: true,
});

//Timer
//let countdown = 3 * 60; //in seconds
//const timerBlock = document.querySelector('#timer');
//const x = setInterval(() => {
//    countdown = countdown - 1;
//    let minutes = Math.floor(countdown / 60);
//    let seconds = Math.floor(countdown - minutes * 60);
//    if (countdown < 0) {
//        timerBlock.innerHTML = 'Expired';
//        clearInterval(x);
//    }
//    timerBlock.innerHTML = `${minutes}:${seconds}`;
//}, 1000);