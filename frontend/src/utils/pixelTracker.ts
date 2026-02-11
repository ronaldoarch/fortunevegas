/**
 * Utilitário para disparar eventos do Facebook Pixel no frontend
 * Isso permite que o Facebook Pixel Helper detecte os eventos
 */

// Declaração global do fbq
declare global {
  interface Window {
    fbq?: (...args: any[]) => void;
    _fbq?: (...args: any[]) => void;
  }
}

/**
 * Inicializa o Facebook Pixel no frontend
 */
export function initFacebookPixel(pixelId: string): void {
  if (!pixelId) {
    console.warn('[PIXEL] Pixel ID não fornecido');
    return;
  }

  // Verificar se já foi inicializado
  if (window.fbq) {
    console.log('[PIXEL] Facebook Pixel já inicializado');
    return;
  }

  // Criar script do Facebook Pixel
  const script = document.createElement('script');
  script.innerHTML = `
    !function(f,b,e,v,n,t,s)
    {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
    n.callMethod.apply(n,arguments):n.queue.push(arguments)};
    if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
    n.queue=[];t=b.createElement(e);t.async=!0;
    t.src=v;s=b.getElementsByTagName(e)[0];
    s.parentNode.insertBefore(t,s)}(window, document,'script',
    'https://connect.facebook.net/en_US/fbevents.js');
    fbq('init', '${pixelId}');
    fbq('track', 'PageView');
  `;
  document.head.appendChild(script);

  console.log(`[PIXEL] Facebook Pixel inicializado com ID: ${pixelId}`);
}

/**
 * Dispara um evento do Facebook Pixel
 */
export function trackPixelEvent(eventName: string, params?: Record<string, any>): void {
  if (!window.fbq) {
    console.warn('[PIXEL] Facebook Pixel não inicializado. Evento não enviado:', eventName);
    return;
  }

  try {
    // Mapear eventos customizados para eventos padrão do Facebook
    const facebookEventName = mapEventName(eventName);
    
    if (params) {
      window.fbq('track', facebookEventName, params);
    } else {
      window.fbq('track', facebookEventName);
    }

    console.log(`[PIXEL] Evento disparado: ${facebookEventName}`, params || {});
  } catch (error) {
    console.error('[PIXEL] Erro ao disparar evento:', error);
  }
}

/**
 * Mapeia eventos customizados para eventos padrão do Facebook
 */
function mapEventName(eventName: string): string {
  const eventMap: Record<string, string> = {
    'registration': 'CompleteRegistration',
    'first_deposit': 'Purchase',
    'redeposit': 'Purchase',
  };

  return eventMap[eventName] || eventName;
}

/**
 * Carrega configurações de pixel do backend e inicializa
 */
export async function loadAndInitPixel(apiUrl: string): Promise<void> {
  try {
    const response = await fetch(`${apiUrl}/api/public/tracking-configs/pixel`);
    if (!response.ok) {
      console.warn('[PIXEL] Não foi possível carregar configurações de pixel');
      return;
    }

    const config = await response.json();
    
    if (config.pixel_id) {
      initFacebookPixel(config.pixel_id);
    } else {
      console.log('[PIXEL] Nenhuma configuração de pixel ativa encontrada');
    }
  } catch (error) {
    console.error('[PIXEL] Erro ao carregar configurações:', error);
  }
}
