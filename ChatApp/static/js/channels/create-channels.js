export const initCreateChannelModal = () => {
  const createChannelModal = document.getElementById("create-channel-modal");
  const openCreateChannelModalButton = document.getElementById("open-create-channel-modal-button");
  // 閉じるボタンのIDをHTMLに合わせて修正
  const closeCreateChannelModalButton = document.getElementById("add-page-close-button");


  console.log("モーダル本体:", createChannelModal);
  console.log("開くボタン:", openCreateChannelModalButton);
  console.log("閉じるボタン:", closeCreateChannelModalButton);


  // モーダル表示ボタンが押された時にモーダルを表示する
  if (openCreateChannelModalButton) { // ボタンが存在するか確認
    openCreateChannelModalButton.addEventListener("click", () => {
      createChannelModal.style.display = "flex"; // CSSで設定したdisplay: none;を上書きして表示
    });
  }

  // モーダル内のXボタンが押された時にモーダルを非表示にする
  if (closeCreateChannelModalButton) { // ボタンが存在するか確認
    closeCreateChannelModalButton.addEventListener("click", () => {
      createChannelModal.style.display = "none";
    });
  }

  // 画面のどこかが押された時にモーダルを非表示にする (モーダル背景クリック)
  addEventListener("click", (e) => {
    if (e.target === createChannelModal) { // クリックされた要素がモーダル自体（背景）なら
      createChannelModal.style.display = "none";
    }
  });

  // create-channel-modalが表示されている時に Ctrl/Command + Enterで送信
  // Enterで自動送信を防ぐ
  document.addEventListener("keydown", keydownEvent);

  function keydownEvent(e) {
    // フォームのname属性 'createChannelForm' を使用して取得
    const channelForm = document.forms.createChannelForm;
    const newChannelTitleInput = channelForm ? channelForm.elements.channelName : null;
    const newChannelTitle = newChannelTitleInput ? newChannelTitleInput.value : '';

    const createChannelModalStyle = getComputedStyle(
      createChannelModal,
      null
    ).getPropertyValue("display");

    if (e.code === "Enter") {
      e.preventDefault(); // Enterキーでの自動送信を防ぐ
    }

    if (
      ((e.ctrlKey && !e.metaKey) || (!e.ctrlKey && e.metaKey)) && // CtrlまたはCommandキー
      e.code === "Enter" // Enterキー
    ) {
      if (createChannelModalStyle !== "none") { // モーダルが表示されている場合
        if (newChannelTitle !== "") { // チャンネル名が空でない場合
          if (channelForm) {
            channelForm.submit(); // フォームを送信
          }
        }
      }
    }
  }
};