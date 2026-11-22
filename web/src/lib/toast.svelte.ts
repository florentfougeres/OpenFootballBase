// Une courte notification (3 s) pour confirmer une action, annoncée aux lecteurs d'écran sans prendre le focus.
export const toast = $state({ text: "", n: 0 });
let timer: ReturnType<typeof setTimeout>;
export function notify(text: string) {
  toast.text = text; toast.n++;
  clearTimeout(timer);
  timer = setTimeout(() => (toast.text = ""), 3000);
}
