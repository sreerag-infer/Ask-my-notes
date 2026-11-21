// mic-processor.js - runs in the browser's audio thread
// It hands every small piece of microphone sound to our page.
class MicProcessor extends AudioWorkletProcessor {
  process(inputs) {
    const samples = inputs[0][0];
    if (samples) this.port.postMessage(samples.slice(0));
    return true;
  }
}

registerProcessor("mic-processor", MicProcessor);
