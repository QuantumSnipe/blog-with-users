document.addEventListener('DOMContentLoaded', async () => {
  if (!('serviceWorker' in navigator)) return;
  const reg = await navigator.serviceWorker.register('/static/js/service-worker.js');
  let sub = await reg.pushManager.getSubscription();
  if (!sub) {
    const key = document.querySelector('meta[name="vapid-key"]').content;
    const converted = urlBase64ToUint8Array(key);
    sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: converted
    });
    await fetch('/subscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(sub)
    });
  }
});

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = atob(base64);
  return Uint8Array.from([...rawData].map(char => char.charCodeAt(0)));
}
