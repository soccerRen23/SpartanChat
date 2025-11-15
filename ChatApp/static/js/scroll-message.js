/*
各チャンネル詳細ページ内、ページ読み込み時に自動で下までスクロールする
*/

const element = document.getElementById("message-area");
const offset = (16 * window.innerHeight) / 100; // 16vhを計算
const elementBottom = element.getBoundingClientRect().bottom;

window.scrollBy({
  top: elementBottom - window.innerHeight + offset,
  behavior: "auto",
});