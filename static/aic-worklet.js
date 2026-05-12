class AicProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super();
    this.blockSize = options.processorOptions.numFrames;
    this.inBuffer = new Float32Array(this.blockSize);
    this.inIdx = 0;
    this.outQueue = [];
    this.outBuffer = null;
    this.outIdx = 0;
    this.port.onmessage = (e) => {
      if (e.data.type === "processed") {
        this.outQueue.push(new Float32Array(e.data.buffer));
      }
    };
  }
  process(inputs, outputs) {
    const input = inputs[0];
    const output = outputs[0];
    if (!output || !output[0]) return true;
    const outCh = output[0];
    const inCh = input && input[0] ? input[0] : null;

    if (inCh) {
      for (let i = 0; i < inCh.length; i++) {
        this.inBuffer[this.inIdx++] = inCh[i];
        if (this.inIdx >= this.blockSize) {
          const copy = new Float32Array(this.inBuffer);
          this.port.postMessage({ type: "frame", buffer: copy.buffer }, [copy.buffer]);
          this.inIdx = 0;
        }
      }
    }

    for (let i = 0; i < outCh.length; i++) {
      if (!this.outBuffer || this.outIdx >= this.outBuffer.length) {
        if (this.outQueue.length > 0) {
          this.outBuffer = this.outQueue.shift();
          this.outIdx = 0;
        } else {
          outCh[i] = 0;
          continue;
        }
      }
      outCh[i] = this.outBuffer[this.outIdx++];
    }
    return true;
  }
}
registerProcessor("aic-processor", AicProcessor);
