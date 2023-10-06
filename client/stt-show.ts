import {LitElement, html, css} from 'lit';
import {customElement, property} from 'lit/decorators.js';
import { webAudioUtils } from './rtc/nexmoProxy.js';

@customElement('stt-show')
export class MyElement extends LitElement {
  @property()
  version = 'STARTING';

  static styles = css`
    textarea {
      width: 100%;
      height: 150px;
      padding: 12px 20px;
      box-sizing: border-box;
      border: 2px solid #ccc;
      border-radius: 4px;
      background-color: #f8f8f8;
      font-size: 16px;
      resize: none;
    }
  `
  firstUpdated(changedProperties) {
    changedProperties.forEach((oldValue, propName) => {
      console.log(`${propName} changed. oldValue: ${oldValue}`);
    });
    const textArea = this.shadowRoot.getElementById("transcript");
    textArea.value="should start making websocket connection.."
    textArea.focus();
  }

  myTemplate = (title)=> html`
    <p>${title}</p>
    <textarea id="transcript">It-athu but-aanal what=yenna?</textarea>
  `;

  render() {
    return this.myTemplate('Transcript')
  }
}