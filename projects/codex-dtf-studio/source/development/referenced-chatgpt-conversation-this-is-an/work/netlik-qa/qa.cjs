var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));

// <stdin>
var tf4 = __toESM(require("@tensorflow/tfjs"));
var wasm = __toESM(require("@tensorflow/tfjs-backend-wasm"));

// node_modules/@upscalerjs/default-model/dist/esm/packages/shared/src/esrgan/esrgan.js
var isTensorArray = (inputs) => {
  return Array.isArray(inputs);
};
var getInput = (inputs) => {
  if (isTensorArray(inputs)) {
    return inputs[0];
  }
  return inputs;
};
var getESRGANModelDefinition = ({ scale, name, version, meta: { architecture, ...meta }, path: modelPath }) => {
  const path2 = modelPath || `models/x${scale}/model.json`;
  if (architecture === "rdn") {
    return {
      scale,
      modelType: "layers",
      _internals: {
        path: path2,
        name,
        version
      },
      meta: {
        architecture,
        ...meta
      },
      inputRange: [0, 255],
      outputRange: [0, 255]
    };
  }
  const setup = (tf5) => {
    const Layer = tf5.layers.Layer;
    const BETA = 0.2;
    class MultiplyBeta extends Layer {
      beta;
      constructor() {
        super({});
        this.beta = BETA;
      }
      call(inputs) {
        return tf5.mul(getInput(inputs), this.beta);
      }
      static className = "MultiplyBeta";
    }
    const getPixelShuffle = (_scale) => {
      class PixelShuffle extends Layer {
        scale = _scale;
        constructor() {
          super({});
        }
        computeOutputShape(inputShape) {
          return [inputShape[0], inputShape[1], inputShape[2], 3];
        }
        call(inputs) {
          return tf5.depthToSpace(getInput(inputs), this.scale, "NHWC");
        }
        static className = `PixelShuffle${scale}x`;
      }
      return PixelShuffle;
    };
    [
      MultiplyBeta,
      getPixelShuffle(scale)
    ].forEach((layer) => {
      tf5.serialization.registerClass(layer);
    });
  };
  return {
    setup,
    scale,
    modelType: "layers",
    _internals: {
      path: path2,
      name,
      version
    },
    meta: {
      architecture,
      ...meta
    },
    inputRange: [0, 1],
    outputRange: [0, 1]
  };
};

// node_modules/@upscalerjs/default-model/dist/esm/models/default-model/src/constants.generated.js
var NAME = "@upscalerjs/default-model";
var VERSION = "1.0.0";

// node_modules/@upscalerjs/default-model/dist/esm/models/default-model/src/index.js
var SCALE = 2;
var modelDefinition = getESRGANModelDefinition({
  scale: SCALE,
  name: NAME,
  version: VERSION,
  path: "models/model.json",
  meta: {
    C: 1,
    D: 2,
    G: 4,
    G0: 64,
    T: 10,
    architecture: "rdn",
    patchSize: 128,
    size: "slim",
    artifactReducing: false,
    sharpening: false,
    dataset: "div2k",
    modelFileName: "rdn-C1-D2-G4-G064-T10-x2-patchsize128-compress100-sharpen0-datadiv2k-vary_cFalse_best-val_loss_epoch494"
  }
});
var src_default = modelDefinition;

// node_modules/upscaler/dist/browser/esm/upscalerjs/src/shared/errors-and-warnings.js
var WARNING_DEPRECATED_MODEL_DEFINITION_URL = "https://upscalerjs.com/documentation/troubleshooting#deprecated-model-definition-function";
var WARNING_DEPRECATED_MODEL_DEFINITION_FN = [
  "Passing a model definition as a function is deprecated and will be removed in a future version.",
  "To leverage model lifecycle methods, use the setup and teardown methods.",
  `For more information, see ${WARNING_DEPRECATED_MODEL_DEFINITION_URL}.`
].join(" ");
var WARNING_UNDEFINED_PADDING_URL = "https://upscalerjs.com/documentation/troubleshooting#padding-is-undefined";
var WARNING_UNDEFINED_PADDING = [
  '"padding" is undefined, but "patchSize" is explicitly defined.',
  "Without padding, patches of images often have visible artifacting at the seams. Defining an explicit padding will resolve the artifacting.",
  `For more information, see ${WARNING_UNDEFINED_PADDING_URL}.`,
  'To hide this warning, pass an explicit padding of "0".'
].join(" ");
var WARNING_PROGRESS_WITHOUT_PATCH_SIZE_URL = "https://upscalerjs.com/documentation/troubleshooting#progress-specified-without-patch-size";
var WARNING_PROGRESS_WITHOUT_PATCH_SIZE = [
  'The "progress" callback was provided but "patchSize" was not defined.',
  'Without a "patchSize", the "progress" callback will never be called.',
  `For more information, see ${WARNING_PROGRESS_WITHOUT_PATCH_SIZE_URL}.`
].join(" ");
var ERROR_INVALID_TENSOR_PREDICTED_URL = "https://upscalerjs.com/documentation/troubleshooting#invalid-predicted-tensor";
var ERROR_INVALID_TENSOR_PREDICTED = (shape) => [
  `The tensor returned by the model was not a valid rank-4 tensor. It's shape is ${JSON.stringify(shape)}.}`,
  "UpscalerJS only supports models returning valid image-like data in four dimensional form.",
  `For more information, see ${ERROR_INVALID_TENSOR_PREDICTED_URL}.`
].join(" ");
var ERROR_INVALID_MODEL_PREDICTION_URL = "https://upscalerjs.com/documentation/troubleshooting#invalid-model-prediction";
var ERROR_INVALID_MODEL_PREDICTION = [
  "The model output was not a valid tensor. UpscalerJS only supports models returning valid tensors.",
  "This is likely an error with the model itself, not UpscalerJS.",
  `For more information, see ${ERROR_INVALID_MODEL_PREDICTION_URL}.`
].join(" ");
var GET_UNDEFINED_TENSORS_ERROR = new Error("No defined tensors were passed to concatTensors");
var AbortError = class extends Error {
  message = "The upscale request received an abort signal";
};
var ERROR_INVALID_MODEL_TYPE_URL = "https://upscalerjs.com/documentation/troubleshooting#invalid-model-type";
var WARNING_INPUT_SIZE_AND_PATCH_SIZE_URL = "https://upscalerjs.com/documentation/troubleshooting#input-size-and-patch-size";
var ERROR_WITH_MODEL_INPUT_SHAPE_URL = "https://upscalerjs.com/documentation/troubleshooting#error-with-model-input-shape";
var ERROR_UNDEFINED_MODEL = new Error("An undefined model was provided to UpscalerJS");
var ERROR_INVALID_MODEL_TYPE = (modelType) => [
  `You've provided an invalid model type: ${JSON.stringify(modelType)}. Accepted types are "layers" and "graph".`,
  `For more information, see ${ERROR_INVALID_MODEL_TYPE_URL}.`
].join(" ");
var ERROR_MODEL_DEFINITION_BUG = (err) => new Error(`There is a bug with the upscaler code. Please report this. ${err ? `Error: ${err}` : ""}`.trim());
var WARNING_INPUT_SIZE_AND_PATCH_SIZE = [
  "You have provided a patchSize, but the model definition already includes an input size.",
  "Your patchSize will be ignored.",
  `For more information, see ${WARNING_INPUT_SIZE_AND_PATCH_SIZE_URL}.`
].join(" ");
var ERROR_WITH_MODEL_INPUT_SHAPE = (inputShape) => [
  `Expected model to have a rank-4 compatible input shape. Instead got: ${JSON.stringify(inputShape)}.`,
  `For more information, see ${ERROR_WITH_MODEL_INPUT_SHAPE_URL}.`
].join(" ");
var GET_INVALID_PATCH_SIZE = (patchSize) => new Error([
  `Invalid patch size: ${patchSize}. Patch size must be greater than 0.`
].join(" "));
var GET_INVALID_PATCH_SIZE_AND_PADDING = (patchSize, padding) => new Error([
  `Invalid patch size and padding: ${patchSize} and ${padding}. Patch size must be greater than padding * 2.`
].join(" "));
var WARNING_PATCH_SIZE_INDIVISIBLE_BY_DIVISIBILITY_FACTOR_URL = "https://upscalerjs.com/documentation/troubleshooting#patch-size-indivisible-by-divisibility-factor";
var GET_WARNING_PATCH_SIZE_INDIVISIBLE_BY_DIVISIBILITY_FACTOR = (patchSize, divisibilityFactor, upscaledPatchSize) => [
  `Invalid patch size: ${patchSize}. The model has a defined divibility factor of ${divisibilityFactor} and patch size must be a multiple of this number.`,
  `Patch size has been scaled up to ${upscaledPatchSize}.`,
  `
For more information, see ${WARNING_PATCH_SIZE_INDIVISIBLE_BY_DIVISIBILITY_FACTOR_URL}.`
].join(" ");
var MODEL_INPUT_SIZE_MUST_BE_SQUARE = new Error([
  "Model input sizes must be square. If you are using a model with a non-square input size and would like to request support,",
  "please file a feature request at https://github.com/thekevinscott/upscalerjs"
].join(" "));
var MODEL_CONFIGURATION_MISSING_PATH_AND_INTERNALS_URL = "https://upscalerjs.com/documentation/troubleshooting#missing-path-and-internals";
var GET_MODEL_CONFIGURATION_MISSING_PATH_AND_INTERNALS = (modelConfiguration) => [
  'Provided model configuration is missing both a "path" and "_internals". A valid path to a model JSON file must be provided.',
  `For more information, see ${MODEL_CONFIGURATION_MISSING_PATH_AND_INTERNALS_URL}.`,
  `The model configuration provided was: ${JSON.stringify(modelConfiguration)}`
].join(" ");

// node_modules/upscaler/dist/browser/esm/shared/src/constants.js
var tf = __toESM(require("@tensorflow/tfjs-core"));
var isShape4D = (shape) => {
  if (!Boolean(shape) || !Array.isArray(shape) || shape.length !== 4) {
    return false;
  }
  return shape.every((value) => value === null || typeof value === "number");
};
var isFixedShape4D = (shape) => isShape4D(shape) && shape[1] !== null && shape[2] !== null && shape[1] > 0 && shape[2] > 0;
function makeIsNDimensionalTensor(rank) {
  function fn(pixels) {
    try {
      return pixels.shape.length === rank;
    } catch (err) {
    }
    return false;
  }
  return fn;
}
var isFourDimensionalTensor = makeIsNDimensionalTensor(4);
var isThreeDimensionalTensor = makeIsNDimensionalTensor(3);
var isTensor = (input) => input instanceof tf.Tensor;
var isString = (el) => typeof el === "string";
var isValidModelType = (modelType) => typeof modelType === "string" && ["layers", "graph"].includes(modelType);
var isNumber = (el) => typeof el === "number";
var isValidRange = (range) => Array.isArray(range) && range.length === 2 && range.every(isNumber);

// node_modules/upscaler/dist/browser/esm/upscalerjs/src/shared/utils.js
var warn = (msg) => {
  console.warn(Array.isArray(msg) ? msg.join("\n") : msg);
};
function isProgress(p) {
  return p !== void 0 && typeof p === "function";
}
function isSingleArgProgress(p) {
  return isProgress(p) && p.length <= 1;
}
var isMultiArgTensorProgress = (p, output, progressOutput) => {
  if (!isProgress(p) || p.length <= 1) {
    return false;
  }
  if (progressOutput === void 0 && output === "tensor") {
    return true;
  }
  return progressOutput === "tensor";
};
var isAborted = (abortSignal) => {
  if (abortSignal) {
    return abortSignal.aborted;
  }
  return false;
};
async function wrapGenerator(gen, postNext) {
  let result;
  for (result = await gen.next(); !result.done; result = await gen.next()) {
    if (postNext) {
      await postNext(result.value);
    }
  }
  return result.value;
}
function nonNullable(value) {
  return value !== null && value !== void 0;
}
function processAndDisposeOfTensor(tf5, tensor, ..._processFns) {
  const processFns = _processFns.filter(nonNullable);
  if (processFns.length) {
    const processedTensor = tf5.tidy(() => processFns.reduce((reducedTensor, processFn) => processFn(reducedTensor), tensor));
    if (!tensor.isDisposed && tensor !== processedTensor) {
      tensor.dispose();
    }
    return processedTensor;
  }
  return tensor;
}
var checkModelDefinition = (modelDefinition2) => {
  if (modelDefinition2 === void 0) {
    throw ERROR_UNDEFINED_MODEL;
  }
  if (!isValidModelType(modelDefinition2.modelType ?? "layers")) {
    throw ERROR_INVALID_MODEL_TYPE(modelDefinition2);
  }
  if (!modelDefinition2.path && !modelDefinition2._internals?.path) {
    throw GET_MODEL_CONFIGURATION_MISSING_PATH_AND_INTERNALS(modelDefinition2);
  }
};

// node_modules/upscaler/dist/browser/esm/upscalerjs/src/shared/makeTick.js
var makeTick = (tf5, signal, awaitNextFrame) => async (result) => {
  if (awaitNextFrame) {
    await tf5.nextFrame();
  }
  if (isAborted(signal)) {
    if (Array.isArray(result)) {
      result.forEach((r) => r?.dispose());
    } else if (isTensor(result)) {
      result.dispose();
    }
    throw new AbortError();
  }
};

// node_modules/upscaler/dist/browser/esm/upscalerjs/src/shared/warmup.js
var isWarmupSizeByPatchSize = (size) => {
  if (!size || typeof size !== "object") {
    return false;
  }
  return "patchSize" in size && typeof size.patchSize === "number";
};
var isNumericWarmupSize = (size) => {
  return Boolean(size) && typeof size === "number" && size > 0;
};
var ERROR_INVALID_WARMUP_VALUE_URL = "https://upscalerjs.com/documentation/troubleshooting#invalid-warmup-value";
var ERROR_INVALID_WARMUP_VALUE = (size) => [
  "Invalid value passed to warmup in warmupSizes:",
  JSON.stringify(size),
  `For more information, see ${ERROR_INVALID_WARMUP_VALUE_URL}.`
].join("\n");
var getInvalidValueError = (size) => new Error(ERROR_INVALID_WARMUP_VALUE(size));
var getWidthAndHeight = (size) => {
  if (isWarmupSizeByPatchSize(size)) {
    const { patchSize } = size;
    return patchSize;
  }
  return size;
};
async function* warmup(tf5, modelPackage, sizes) {
  const { model, modelDefinition: modelDefinition2 } = await modelPackage;
  for (const size of sizes) {
    if (!isWarmupSizeByPatchSize(size) && !isNumericWarmupSize(size)) {
      throw getInvalidValueError(size);
    }
    const warmupSize = getWidthAndHeight(size);
    let dummyTensor = tf5.zeros([1, warmupSize, warmupSize, 3]);
    yield [dummyTensor];
    const fns = [
      modelDefinition2.preprocess,
      (t) => model.predict(t),
      modelDefinition2.postprocess
    ].filter(Boolean);
    for (const fn of fns) {
      dummyTensor = processAndDisposeOfTensor(tf5, dummyTensor, fn);
      yield [dummyTensor];
    }
    dummyTensor.dispose();
    yield;
  }
}
var getSizesAsArray = (sizes) => {
  if (Array.isArray(sizes)) {
    for (const size of sizes) {
      if (!isWarmupSizeByPatchSize(size) && !isNumericWarmupSize(size)) {
        throw getInvalidValueError(sizes);
      }
    }
    return sizes;
  } else if (isWarmupSizeByPatchSize(sizes) || isNumericWarmupSize(sizes)) {
    return [sizes];
  }
  throw getInvalidValueError(sizes);
};
var cancellableWarmup = async (tf5, modelPackage, sizes, { signal = void 0, awaitNextFrame = false } = {}, internalArgs) => {
  const tick = makeTick(tf5, signal || internalArgs.signal, awaitNextFrame);
  await tick();
  await wrapGenerator(warmup(tf5, modelPackage, getSizesAsArray(sizes)), tick);
};

// node_modules/upscaler/dist/browser/esm/upscalerjs/src/shared/isLayersModel.js
var isLayersModel = (tf5, model) => model instanceof tf5.LayersModel;

// node_modules/upscaler/dist/browser/esm/upscalerjs/src/shared/model-utils.js
var parseModelDefinition = (modelDefinition2) => ({
  ...modelDefinition2
});
function isModelDefinitionFn(modelDefinition2) {
  return typeof modelDefinition2 === "function";
}
function getModelDefinitionOrModelDefinitionFnAsModelDefinition(tf5, modelDefinition2) {
  if (isModelDefinitionFn(modelDefinition2)) {
    warn(WARNING_DEPRECATED_MODEL_DEFINITION_FN);
    return modelDefinition2(tf5);
  }
  return modelDefinition2;
}
async function getModel(tf5, modelDefinition2) {
  const modelDef = getModelDefinitionOrModelDefinitionFnAsModelDefinition(tf5, modelDefinition2);
  if (modelDef.setup) {
    await modelDef.setup(tf5);
  }
  return modelDef;
}
function loadTfModel(tf5, modelPath, modelType) {
  if (modelType === "graph") {
    return tf5.loadGraphModel(modelPath);
  }
  return tf5.loadLayersModel(modelPath);
}
var getBatchInputShape = (tf5, model) => {
  if (isLayersModel(tf5, model)) {
    return model.layers[0].batchInputShape;
  }
  return model.inputs[0].shape;
};
var getModelInputShape = (tf5, { model }) => {
  const batchInputShape = getBatchInputShape(tf5, model);
  if (!isShape4D(batchInputShape)) {
    throw new Error(ERROR_WITH_MODEL_INPUT_SHAPE(batchInputShape));
  }
  return batchInputShape;
};
var getPatchSizeAsMultiple = (divisibilityFactor, patchSize) => {
  return Math.ceil(patchSize / divisibilityFactor) * divisibilityFactor;
};
var parsePatchAndInputShapes = (tf5, modelPackage, { patchSize, padding }, imageSize) => {
  const modelInputShape = getModelInputShape(tf5, modelPackage);
  if (patchSize !== void 0) {
    if (patchSize <= 0) {
      throw GET_INVALID_PATCH_SIZE(patchSize);
    }
    if (padding !== void 0 && padding * 2 >= patchSize) {
      throw GET_INVALID_PATCH_SIZE_AND_PADDING(patchSize, padding);
    }
  }
  if (isFixedShape4D(modelInputShape)) {
    if (patchSize !== void 0) {
      warn(WARNING_INPUT_SIZE_AND_PATCH_SIZE);
    }
    if (modelInputShape[1] !== modelInputShape[2]) {
      throw MODEL_INPUT_SIZE_MUST_BE_SQUARE;
    }
    return {
      patchSize: modelInputShape[1],
      padding,
      modelInputShape
    };
  }
  if (patchSize !== void 0 && padding === void 0) {
    warn(WARNING_UNDEFINED_PADDING);
  }
  const { divisibilityFactor } = modelPackage.modelDefinition;
  if (divisibilityFactor !== void 0) {
    if (patchSize !== void 0) {
      const multipliedPatchSize = getPatchSizeAsMultiple(divisibilityFactor, patchSize);
      if (multipliedPatchSize !== patchSize) {
        warn(GET_WARNING_PATCH_SIZE_INDIVISIBLE_BY_DIVISIBILITY_FACTOR(patchSize, divisibilityFactor, multipliedPatchSize));
      }
      return {
        patchSize: multipliedPatchSize,
        padding,
        modelInputShape: [null, multipliedPatchSize, multipliedPatchSize, 3]
      };
    }
    return {
      patchSize: void 0,
      padding: void 0,
      modelInputShape: [
        null,
        getPatchSizeAsMultiple(divisibilityFactor, imageSize[1]),
        getPatchSizeAsMultiple(divisibilityFactor, imageSize[2]),
        3
      ]
    };
  }
  return {
    patchSize,
    padding,
    modelInputShape: void 0
  };
};

// node_modules/upscaler/dist/browser/esm/upscalerjs/src/shared/tensor-utils.js
var padInput = (tf5, inputShape) => (pixels) => {
  const pixelsHeight = pixels.shape[1];
  const pixelsWidth = pixels.shape[2];
  if (isFixedShape4D(inputShape) && (inputShape[1] > pixelsHeight || inputShape[2] > pixelsWidth)) {
    return tf5.tidy(() => {
      const height = Math.max(pixelsHeight, inputShape[1]);
      const width = Math.max(pixelsWidth, inputShape[2]);
      const rightTensor = tf5.zeros([1, pixelsHeight, width - pixelsWidth, 3]);
      const bottomTensor = tf5.zeros([1, height - pixelsHeight, width, 3]);
      const topTensor = tf5.concat([pixels, rightTensor], 2);
      const final = tf5.concat([topTensor, bottomTensor], 1);
      return final;
    });
  }
  return pixels;
};
var trimInput = (tf5, imageSize, scale) => (pixels) => {
  const height = imageSize[1] * scale;
  const width = imageSize[2] * scale;
  if (height < pixels.shape[1] || width < pixels.shape[2]) {
    return tf5.tidy(() => tf5.slice(pixels, [0, 0, 0], [1, height, width, 3]));
  }
  return pixels;
};
var scaleOutput = (range) => (pixels) => {
  const endingRange = isValidRange(range) ? range[1] : 255;
  return pixels.clipByValue(0, endingRange).mul(endingRange === 1 ? 255 : 1);
};
var scaleIncomingPixels = (tf5, range) => (tensor) => {
  if (isValidRange(range) && range[1] === 1) {
    return tf5.mul(tensor, 1 / 255);
  }
  return tensor;
};
var tensorAsClampedArray = (tf5, tensor) => tf5.tidy(() => {
  const [height, width] = tensor.shape;
  const fill = tf5.fill([height, width], 255).expandDims(2);
  return tensor.clipByValue(0, 255).concat([fill], 2).dataSync();
});
function getCopyOfInput(input) {
  return isTensor(input) ? input.clone() : input;
}
function concatTensors(tf5, tensors, axis = 0) {
  const definedTensors = tensors.filter(nonNullable);
  if (definedTensors.length === 0) {
    throw GET_UNDEFINED_TENSORS_ERROR;
  }
  const concatenatedTensor = tf5.concat(definedTensors, axis);
  tensors.forEach((tensor) => tensor?.dispose());
  return concatenatedTensor;
}

// node_modules/upscaler/dist/browser/esm/upscalerjs/src/shared/image-utils.js
var get1DPatch = (total, idx, patchSize, padding) => {
  let preOrigin = idx;
  const prePadding = idx === 0 ? 0 : patchSize === total ? 0 : padding;
  const isBeyondBounds = preOrigin + patchSize > total;
  let postOrigin = isBeyondBounds ? patchSize - (total - preOrigin) : 0;
  const postPadding = isBeyondBounds ? 0 : patchSize === total ? 0 : padding;
  const prePaddingAdjusted = isBeyondBounds ? 0 : prePadding;
  let postSize = patchSize - (isBeyondBounds ? postOrigin : 0);
  if (isBeyondBounds) {
    preOrigin = total - patchSize;
  }
  preOrigin -= prePaddingAdjusted;
  postOrigin += prePaddingAdjusted;
  postSize -= prePaddingAdjusted + postPadding;
  const increment = patchSize > total ? total : patchSize - prePadding - postPadding;
  return {
    pre: {
      origin: preOrigin,
      size: patchSize
    },
    post: {
      origin: postOrigin,
      size: postSize
    },
    increment
  };
};
var getPatchesFromImage = ([width, height], patchSize, padding) => {
  const patches = [];
  let x = 0;
  let y = 0;
  while (y < height) {
    const { pre: { origin: preOriginY, size: preSizeY }, post: { origin: postOriginY, size: postSizeY }, increment: yIncrement } = get1DPatch(height, y, Math.min(patchSize, height), padding);
    const row = [];
    while (x < width) {
      const { pre: { origin: preOriginX, size: preSizeX }, post: { origin: postOriginX, size: postSizeX }, increment: xIncrement } = get1DPatch(width, x, Math.min(patchSize, width), padding);
      row.push({
        pre: {
          origin: [preOriginY, preOriginX],
          size: [preSizeY, preSizeX]
        },
        post: {
          origin: [postOriginY, postOriginX],
          size: [postSizeY, postSizeX]
        }
      });
      x += xIncrement;
    }
    patches.push(row);
    x = 0;
    y += yIncrement;
  }
  return patches;
};

// node_modules/upscaler/dist/browser/esm/upscalerjs/src/shared/upscale.js
var getPercentageComplete = (row, col, columns, total) => {
  const index = row * columns + col + 1;
  const percent = index / total;
  return percent;
};
var executeModel = (model, pixels) => {
  const predictedPixels = model.predict(pixels);
  if (!isTensor(predictedPixels)) {
    throw new Error(ERROR_INVALID_MODEL_PREDICTION);
  }
  if (isFourDimensionalTensor(predictedPixels)) {
    return predictedPixels;
  }
  throw new Error(ERROR_INVALID_TENSOR_PREDICTED(predictedPixels.shape));
};
async function* processPixels(tf5, pixels, { output, progress, progressOutput }, modelPackage, { originalImageSize, patchSize, padding = 0 }, { tensorAsBase64: tensorAsBase642 }) {
  const { model, modelDefinition: modelDefinition2 } = modelPackage;
  const scale = modelDefinition2.scale ?? 1;
  if (patchSize) {
    const [height, width] = pixels.shape.slice(1);
    const patches = getPatchesFromImage([width, height], patchSize, padding);
    yield;
    let upscaledTensor;
    const total = patches.length * patches[0].length;
    for (let rowIdx = 0; rowIdx < patches.length; rowIdx++) {
      const row = patches[rowIdx];
      const columns = row.length;
      let colTensor;
      yield [colTensor, upscaledTensor];
      for (let colIdx = 0; colIdx < columns; colIdx++) {
        const { pre, post } = row[colIdx];
        yield [upscaledTensor, colTensor];
        const slicedPixels = pixels.slice([0, ...pre.origin], [-1, ...pre.size]);
        yield [upscaledTensor, colTensor, slicedPixels];
        const prediction2 = executeModel(model, slicedPixels);
        slicedPixels.dispose();
        yield [upscaledTensor, colTensor, prediction2];
        const startSlice = [0, post.origin[0] * scale, post.origin[1] * scale];
        const endSlice = [-1, post.size[0] * scale, post.size[1] * scale];
        const slicedPrediction = prediction2.slice(startSlice, endSlice);
        prediction2.dispose();
        yield [upscaledTensor, colTensor, slicedPrediction];
        const processedPrediction = processAndDisposeOfTensor(tf5, slicedPrediction, modelDefinition2.postprocess, scaleOutput(modelDefinition2.outputRange));
        yield [upscaledTensor, colTensor, processedPrediction];
        if (progress !== void 0 && isProgress(progress)) {
          const percent = getPercentageComplete(rowIdx, colIdx, columns, total);
          if (isSingleArgProgress(progress)) {
            progress(percent);
          } else {
            const squeezedTensor3 = processedPrediction.squeeze();
            const sliceData = {
              row: rowIdx,
              col: colIdx,
              patchCoordinates: {
                pre,
                post
              }
            };
            if (isMultiArgTensorProgress(progress, output, progressOutput)) {
              progress(percent, squeezedTensor3, sliceData);
            } else {
              const src = tensorAsBase642(tf5, squeezedTensor3);
              squeezedTensor3.dispose();
              progress(percent, src, sliceData);
            }
          }
        }
        yield [upscaledTensor, colTensor, processedPrediction];
        colTensor = concatTensors(tf5, [colTensor, processedPrediction], 2);
        processedPrediction.dispose();
        yield [upscaledTensor, colTensor];
      }
      upscaledTensor = concatTensors(tf5, [upscaledTensor, colTensor], 1);
      colTensor.dispose();
      yield [upscaledTensor];
    }
    const processedUpscaledTensor = processAndDisposeOfTensor(tf5, upscaledTensor.clone(), trimInput(tf5, originalImageSize, scale));
    upscaledTensor?.dispose();
    yield [processedUpscaledTensor];
    const squeezedTensor2 = processedUpscaledTensor.squeeze();
    processedUpscaledTensor.dispose();
    return squeezedTensor2;
  }
  if (progress) {
    warn(WARNING_PROGRESS_WITHOUT_PATCH_SIZE);
  }
  const prediction = executeModel(model, pixels);
  yield [prediction];
  const postprocessedTensor = processAndDisposeOfTensor(tf5, prediction.clone(), modelDefinition2.postprocess, scaleOutput(modelDefinition2.outputRange), trimInput(tf5, originalImageSize, scale));
  prediction.dispose();
  yield [postprocessedTensor];
  const squeezedTensor = postprocessedTensor.squeeze();
  postprocessedTensor.dispose();
  return squeezedTensor;
}
async function* upscale(tf5, input, args, modelPackage, { getImageAsTensor: getImageAsTensor2, tensorAsBase64: tensorAsBase642 }) {
  const parsedInput = getCopyOfInput(input);
  const startingPixels = await getImageAsTensor2(tf5, parsedInput);
  yield startingPixels;
  const imageSize = startingPixels.shape;
  const { patchSize, padding, modelInputShape } = parsePatchAndInputShapes(tf5, modelPackage, args, imageSize);
  const preprocessedPixels = processAndDisposeOfTensor(tf5, startingPixels, modelPackage.modelDefinition.preprocess, scaleIncomingPixels(tf5, modelPackage.modelDefinition.inputRange), modelInputShape ? padInput(tf5, modelInputShape) : void 0);
  yield preprocessedPixels;
  const gen = processPixels(tf5, preprocessedPixels, {
    output: args.output,
    progressOutput: args.progressOutput,
    progress: args.progress
  }, modelPackage, {
    originalImageSize: imageSize,
    patchSize,
    padding
  }, {
    tensorAsBase64: tensorAsBase642
  });
  let result = await gen.next();
  yield result.value;
  while (!result.done) {
    result = await gen.next();
    if (Array.isArray(result.value)) {
      yield [...result.value, preprocessedPixels];
    } else if (isTensor(result.value)) {
      yield [result.value, preprocessedPixels];
    } else {
      yield preprocessedPixels;
    }
  }
  preprocessedPixels.dispose();
  const upscaledPixels = result.value;
  if (args.output === "tensor") {
    return upscaledPixels;
  }
  const base64Src = tensorAsBase642(tf5, upscaledPixels);
  upscaledPixels.dispose();
  return base64Src;
}
async function cancellableUpscale(tf5, input, { signal, awaitNextFrame, ...args }, internalArgs, { checkValidEnvironment: checkValidEnvironment2, ...internalConfig }) {
  checkValidEnvironment2(input, {
    output: args.output,
    progressOutput: args.progressOutput
  });
  const tick = makeTick(tf5, signal || internalArgs.signal, awaitNextFrame);
  await tick();
  const upscaledPixels = await wrapGenerator(upscale(tf5, input, args, internalArgs, internalConfig), tick);
  await tick();
  return upscaledPixels;
}

// node_modules/upscaler/dist/browser/esm/upscalerjs/src/shared/upscaler.js
var DEFAULT_MODEL = src_default;
function getUpscaler({ tf: tf5, getUpscaleOptions: getUpscaleOptions2, checkValidEnvironment: checkValidEnvironment2, getImageAsTensor: getImageAsTensor2, tensorAsBase64: tensorAsBase642, loadModel: loadModel2 }) {
  class Upscaler {
    _opts;
    _model;
    ready;
    _abortController = new AbortController();
    constructor(opts = {}) {
      this._opts = {
        ...opts
      };
      this._model = loadModel2(tf5, getModel(tf5, this._opts.model || DEFAULT_MODEL));
      this.ready = new Promise((resolve, reject) => {
        this._model.then(() => cancellableWarmup(tf5, this._model, this._opts.warmupSizes || [], void 0, {
          signal: this._abortController.signal
        })).then(resolve).catch(reject);
      });
    }
    async execute(image, options) {
      const internals = {
        checkValidEnvironment: checkValidEnvironment2,
        getImageAsTensor: getImageAsTensor2,
        tensorAsBase64: tensorAsBase642
      };
      await this.ready;
      const modelPackage = await this._model;
      return cancellableUpscale(tf5, image, getUpscaleOptions2(options), {
        ...modelPackage,
        signal: this._abortController.signal
      }, internals);
    }
    upscale = this.execute.bind(this);
    warmup = async (warmupSizes = [], options) => {
      await this.ready;
      return cancellableWarmup(tf5, this._model, warmupSizes, options, {
        signal: this._abortController.signal
      });
    };
    abort = () => {
      this._abortController.abort();
      this._abortController = new AbortController();
    };
    dispose = async () => {
      await this.ready;
      const { model, modelDefinition: modelDefinition2 } = await this._model;
      if (modelDefinition2.teardown) {
        await modelDefinition2.teardown(tf5);
      }
      model.dispose();
    };
    getModel = () => this._model;
  }
  ;
  return Upscaler;
}

// node_modules/upscaler/dist/browser/esm/upscalerjs/src/browser/index.js
var tf3 = __toESM(require("@tensorflow/tfjs"));

// node_modules/upscaler/dist/browser/esm/upscalerjs/src/browser/args.browser.js
var getOutputOption = (output) => {
  if (output === "tensor") {
    return "tensor";
  }
  return "base64";
};
var getUpscaleOptions = ({ output, progressOutput, ...options } = {}) => {
  return {
    ...options,
    output: getOutputOption(output),
    progressOutput: getOutputOption(progressOutput || output)
  };
};

// node_modules/upscaler/dist/browser/esm/upscalerjs/src/browser/loadModel.browser.js
var CDN_PATH_DEFINITIONS = {
  "jsdelivr": (packageName, version, path2) => `https://cdn.jsdelivr.net/npm/${packageName}@${version}/${path2}`,
  "unpkg": (packageName, version, path2) => `https://unpkg.com/${packageName}@${version}/${path2}`
};
var CDNS = [
  "jsdelivr",
  "unpkg"
];
var getLoadModelErrorMessage = (errs, modelPath, internals) => new Error([
  `Could not resolve URL ${modelPath} for package ${internals?.name}@${internals?.version}`,
  "Errors include:",
  ...errs.map(([cdn, err]) => `- ${cdn}: ${err.message}`)
].join("\n"));
async function fetchModel(tf5, modelConfiguration) {
  const { modelType, _internals, path: modelPath } = modelConfiguration;
  if (modelPath) {
    return await loadTfModel(tf5, modelPath, modelType);
  }
  if (!_internals) {
    throw ERROR_MODEL_DEFINITION_BUG("Missing internals");
  }
  const errs = [];
  for (const cdn of CDNS) {
    const getCDNFn = CDN_PATH_DEFINITIONS[cdn];
    try {
      const url = getCDNFn(_internals.name, _internals.version, _internals.path);
      return await loadTfModel(tf5, url, modelType);
    } catch (err) {
      errs.push([cdn, err instanceof Error ? err : new Error(`There was an unknown error: ${JSON.stringify(err)}`)]);
    }
  }
  throw getLoadModelErrorMessage(errs, modelPath || _internals.path, _internals);
}
var loadModel = async (tf5, _modelDefinition) => {
  const modelDefinition2 = await _modelDefinition;
  checkModelDefinition(modelDefinition2);
  const parsedModelDefinition = parseModelDefinition(modelDefinition2);
  const model = await fetchModel(tf5, parsedModelDefinition);
  return {
    model,
    modelDefinition: parsedModelDefinition
  };
};

// node_modules/upscaler/dist/browser/esm/upscalerjs/src/browser/image.browser.js
var tf2 = __toESM(require("@tensorflow/tfjs"));
var ERROR_ENVIRONMENT_DISALLOWS_BASE64_URL = "https://upscalerjs.com/documentation/troubleshooting#environment-disallows-base64";
var ERROR_ENVIRONMENT_DISALLOWS_STRING_INPUT_URL = "https://upscalerjs.com/documentation/troubleshooting#environment-disallows-string-input";
var getEnvironmentDisallowsStringInput = () => new Error([
  "Environment does not support a string URL as an input format.",
  `For more information, see ${ERROR_ENVIRONMENT_DISALLOWS_STRING_INPUT_URL}.`
].join("\n"));
var getEnvironmentDisallowsBase64 = () => new Error([
  "Environment does not support base64 as an output format.",
  `For more information, see ${ERROR_ENVIRONMENT_DISALLOWS_BASE64_URL}.`
].join("\n"));
var getInvalidTensorError = (input) => new Error([
  `Unsupported dimensions for incoming pixels: ${input.shape.length}.`,
  "Only 3 or 4 rank tensors are supported."
].join("\n"));
var getInvalidImageError = () => new Error([
  "Failed to load image"
].join(" "));
var loadImage = (src) => new Promise((resolve, reject) => {
  const img = new Image();
  img.src = src;
  img.crossOrigin = "anonymous";
  img.onload = () => resolve(img);
  img.onerror = () => reject(getInvalidImageError());
});
var fromPixels = (input) => tf2.browser.fromPixelsAsync(input);
var getTensorFromInput = async (input, _tf) => {
  if (isTensor(input)) {
    return input;
  }
  if (isString(input)) {
    const imgHTMLElement = await loadImage(input);
    return fromPixels(imgHTMLElement);
  }
  return fromPixels(input);
};
var getImageAsTensor = async (tf5, input) => {
  const tensor = await getTensorFromInput(input, tf5);
  if (isThreeDimensionalTensor(tensor)) {
    const expandedTensor = tensor.expandDims(0);
    tensor.dispose();
    return expandedTensor;
  }
  if (isFourDimensionalTensor(tensor)) {
    return tensor;
  }
  throw getInvalidTensorError(tensor);
};
var tensorAsBase64 = (tf5, tensor) => {
  const arr = tensorAsClampedArray(tf5, tensor);
  const [height, width] = tensor.shape;
  const imageData = new ImageData(width, height);
  imageData.data.set(arr);
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    throw new Error("No context found");
  }
  ctx.putImageData(imageData, 0, 0);
  return canvas.toDataURL();
};
var checkIfValidEnvironment = (errFn) => {
  try {
    if ((new Image() && "createElement" in document) !== true) {
      throw errFn();
    }
  } catch (err) {
    throw errFn();
  }
};
var checkValidEnvironment = (input, { output = "base64", progressOutput }) => {
  if (typeof input === "string") {
    checkIfValidEnvironment(getEnvironmentDisallowsStringInput);
  }
  if (progressOutput === "base64" || output === "base64") {
    checkIfValidEnvironment(getEnvironmentDisallowsBase64);
  }
};

// node_modules/upscaler/dist/browser/esm/upscalerjs/src/browser/index.js
var browser_default = getUpscaler({
  tf: tf3,
  getUpscaleOptions,
  loadModel,
  getImageAsTensor,
  tensorAsBase64,
  checkValidEnvironment
});

// node_modules/@upscalerjs/esrgan-slim/dist/esm/packages/shared/src/esrgan/esrgan.js
var isTensorArray2 = (inputs) => {
  return Array.isArray(inputs);
};
var getInput2 = (inputs) => {
  if (isTensorArray2(inputs)) {
    return inputs[0];
  }
  return inputs;
};
var getESRGANModelDefinition2 = ({ scale, name, version, meta: { architecture, ...meta }, path: modelPath }) => {
  const path2 = modelPath || `models/x${scale}/model.json`;
  if (architecture === "rdn") {
    return {
      scale,
      modelType: "layers",
      _internals: {
        path: path2,
        name,
        version
      },
      meta: {
        architecture,
        ...meta
      },
      inputRange: [0, 255],
      outputRange: [0, 255]
    };
  }
  const setup = (tf5) => {
    const Layer = tf5.layers.Layer;
    const BETA = 0.2;
    class MultiplyBeta extends Layer {
      beta;
      constructor() {
        super({});
        this.beta = BETA;
      }
      call(inputs) {
        return tf5.mul(getInput2(inputs), this.beta);
      }
      static className = "MultiplyBeta";
    }
    const getPixelShuffle = (_scale) => {
      class PixelShuffle extends Layer {
        scale = _scale;
        constructor() {
          super({});
        }
        computeOutputShape(inputShape) {
          return [inputShape[0], inputShape[1], inputShape[2], 3];
        }
        call(inputs) {
          return tf5.depthToSpace(getInput2(inputs), this.scale, "NHWC");
        }
        static className = `PixelShuffle${scale}x`;
      }
      return PixelShuffle;
    };
    [
      MultiplyBeta,
      getPixelShuffle(scale)
    ].forEach((layer) => {
      tf5.serialization.registerClass(layer);
    });
  };
  return {
    setup,
    scale,
    modelType: "layers",
    _internals: {
      path: path2,
      name,
      version
    },
    meta: {
      architecture,
      ...meta
    },
    inputRange: [0, 1],
    outputRange: [0, 1]
  };
};

// node_modules/@upscalerjs/esrgan-slim/dist/esm/models/esrgan-slim/src/constants.generated.js
var NAME2 = "@upscalerjs/esrgan-slim";
var VERSION2 = "1.0.0";

// node_modules/@upscalerjs/esrgan-slim/dist/esm/models/esrgan-slim/src/getModelDefinition.js
var getModelDefinition = (scale, modelFileName) => getESRGANModelDefinition2({
  scale,
  path: `models/x${scale}/model.json`,
  name: NAME2,
  version: VERSION2,
  meta: {
    C: 1,
    D: 2,
    G: 4,
    G0: 64,
    T: 10,
    architecture: "rdn",
    patchSize: scale === 3 ? 129 : 128,
    size: "slim",
    artifactReducing: false,
    sharpening: false,
    dataset: "div2k",
    modelFileName
  }
});
var getModelDefinition_default = getModelDefinition;

// node_modules/@upscalerjs/esrgan-slim/dist/esm/models/esrgan-slim/src/x2/index.js
var x2_default = getModelDefinition_default(2, "rdn-C1-D2-G4-G064-T10-x2-patchsize128-compress100-sharpen0-datadiv2k-vary_cFalse_best-val_loss_epoch494");

// <stdin>
var import_sharp = __toESM(require("sharp"));
var import_promises = require("node:fs/promises");
var import_node_path = __toESM(require("node:path"));

// src/matte.mjs
var clamp = (n) => Math.max(0, Math.min(1, n));
function contractAlpha1px(image) {
  const { width: w, height: h } = image, source = image.data, data = new Uint8ClampedArray(source);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const k = (y * w + x) * 4;
    let alpha = 0;
    if (x > 0 && y > 0 && x < w - 1 && y < h - 1) {
      alpha = 255;
      for (let yy = y - 1; yy <= y + 1; yy++) for (let xx = x - 1; xx <= x + 1; xx++) alpha = Math.min(alpha, source[(yy * w + xx) * 4 + 3]);
    }
    data[k + 3] = alpha;
    if (!alpha) data[k] = data[k + 1] = data[k + 2] = 0;
  }
  return { data, width: w, height: h };
}
function cleanMatte(image, strength = 1) {
  const { width: w, height: h } = image, data = new Uint8ClampedArray(image.data), n = w * h;
  if (!strength) return { data, width: w, height: h };
  const low = 6 + strength * 5, high = 245 - strength * 5, seen = new Uint8Array(n), queue = new Int32Array(n);
  const maxDust = Math.min(12, Math.max(2, Math.floor(n / 3e5)));
  for (let start = 0; start < n; start++) if (data[start * 4 + 3] > low && !seen[start]) {
    let head = 0, tail = 1;
    queue[0] = start;
    seen[start] = 1;
    while (head < tail) {
      const k = queue[head++], x = k % w, y = Math.floor(k / w);
      for (const q of [x > 0 ? k - 1 : -1, x < w - 1 ? k + 1 : -1, y > 0 ? k - w : -1, y < h - 1 ? k + w : -1]) if (q >= 0 && !seen[q] && data[q * 4 + 3] > low) {
        seen[q] = 1;
        queue[tail++] = q;
      }
    }
    let strongest = 0;
    for (let i = 0; i < tail; i++) strongest = Math.max(strongest, data[queue[i] * 4 + 3]);
    if (tail <= maxDust && strongest < 200) for (let i = 0; i < tail; i++) data[queue[i] * 4 + 3] = 0;
  }
  for (let i = 3; i < data.length; i += 4) {
    const t = clamp((data[i] - low) / (high - low));
    data[i] = Math.round(255 * t);
    if (!data[i]) data[i - 3] = data[i - 2] = data[i - 1] = 0;
  }
  return { data, width: w, height: h };
}

// src/photo-extract.mjs
var clamp2 = (n, a, b) => Math.max(a, Math.min(b, n));
var median = (a) => {
  a.sort((x, y) => x - y);
  return a[Math.floor(a.length / 2)] || 0;
};
function solve3(a, b) {
  const m = a.map((r, i) => [...r, b[i]]);
  for (let k = 0; k < 3; k++) {
    let p = k;
    for (let j = k + 1; j < 3; j++) if (Math.abs(m[j][k]) > Math.abs(m[p][k])) p = j;
    [m[k], m[p]] = [m[p], m[k]];
    if (Math.abs(m[k][k]) < 1e-9) return [b[0] / Math.max(1, a[0][0]), 0, 0];
    const v = m[k][k];
    for (let j = k; j < 4; j++) m[k][j] /= v;
    for (let i = 0; i < 3; i++) if (i !== k) {
      const z = m[i][k];
      for (let j = k; j < 4; j++) m[i][j] -= z * m[k][j];
    }
  }
  return m.map((r) => r[3]);
}
function isolatePrint({ data, width: w, height: h }, region, tolerance = 28, { contract = true, inkMode = "auto" } = {}) {
  const x0 = clamp2(Math.floor(region.x), 0, w - 1), y0 = clamp2(Math.floor(region.y), 0, h - 1), cw = clamp2(Math.ceil(region.width), 1, w - x0), ch = clamp2(Math.ceil(region.height), 1, h - y0);
  const border = [], step = Math.max(1, Math.floor(Math.min(cw, ch) / 90)), edge = Math.max(2, Math.round(Math.min(cw, ch) * 0.07));
  for (let y = 0; y < ch; y += step) for (let x = 0; x < cw; x += step) if (x < edge || y < edge || x >= cw - edge || y >= ch - edge) {
    const k = ((y + y0) * w + x + x0) * 4;
    if (data[k + 3] > 200) border.push({ v: [1, x / cw - 0.5, y / ch - 0.5], rgb: [data[k], data[k + 1], data[k + 2]] });
  }
  if (border.length < 9) throw new Error("Kuma\u015F zemini \xF6l\xE7\xFClemedi. Bask\u0131n\u0131n \xE7evresinde biraz bo\u015F kuma\u015F b\u0131rak\u0131n.");
  const mid = [0, 1, 2].map((c) => median(border.map((p) => p.rgb[c])));
  let samples = border.filter((p) => Math.hypot(...p.rgb.map((v, c) => v - mid[c])) < 55);
  if (samples.length < 9) samples = border;
  let planes;
  for (let pass = 0; pass < 3; pass++) {
    const a = Array.from({ length: 3 }, () => [0, 0, 0]), b = Array.from({ length: 3 }, () => [0, 0, 0]);
    for (const p of samples) for (let i = 0; i < 3; i++) {
      for (let j = 0; j < 3; j++) a[i][j] += p.v[i] * p.v[j];
      for (let c = 0; c < 3; c++) b[c][i] += p.v[i] * p.rgb[c];
    }
    planes = b.map((v) => solve3(a, v));
    const next = samples.filter((p) => Math.hypot(...p.rgb.map((v, c) => v - planes[c].reduce((s, q, i) => s + q * p.v[i], 0))) < 32);
    if (next.length < 9) break;
    samples = next;
  }
  const bright = [], sampleStep = Math.max(1, Math.ceil(Math.sqrt(cw * ch / 6e4)));
  let neutral = 0;
  for (let y = 0; y < ch; y += sampleStep) for (let x = 0; x < cw; x += sampleStep) {
    const p = ((y + y0) * w + x + x0) * 4, v = [1, x / cw - 0.5, y / ch - 0.5], bg = planes.map((c) => c.reduce((s, z, i) => s + z * v[i], 0)), rgb = [data[p], data[p + 1], data[p + 2]], lift = rgb.reduce((s, z, c) => s + z - bg[c], 0) / 3;
    if (lift > 40 && data[p + 3] > 200) {
      bright.push(rgb);
      if (Math.max(...rgb) - Math.min(...rgb) < 55) neutral++;
    }
  }
  const light = inkMode === "light" || inkMode === "auto" && bright.length >= 20 && neutral / bright.length > 0.94;
  const ordered = bright.sort((a, b) => b.reduce((s, v) => s + v, 0) - a.reduce((s, v) => s + v, 0)), top = ordered.slice(0, Math.max(3, Math.ceil(ordered.length * 0.06)));
  const ink = [0, 1, 2].map((c) => top.length ? median(top.map((v) => v[c])) : 240);
  let output = new Uint8ClampedArray(cw * ch * 4);
  const low = clamp2(Number(tolerance) || 28, 8, 100), high = low + 23;
  let count = 0, minX = cw, minY = ch, maxX = -1, maxY = -1;
  for (let y = 0; y < ch; y++) for (let x = 0; x < cw; x++) {
    const p = ((y + y0) * w + x + x0) * 4, q = (y * cw + x) * 4, v = [1, x / cw - 0.5, y / ch - 0.5], bg = planes.map((c) => clamp2(c.reduce((s, z, i) => s + z * v[i], 0), 0, 255)), dist = Math.hypot(data[p] - bg[0], data[p + 1] - bg[1], data[p + 2] - bg[2]);
    let a;
    if (light) {
      const direction = ink.map((z, c) => z - bg[c]), energy = direction.reduce((s, z) => s + z * z, 0), projection = direction.reduce((s, z, c) => s + z * (data[p + c] - bg[c]), 0) / Math.max(1, energy), floor = low * 0.22 / Math.max(20, Math.sqrt(energy / 3));
      a = clamp2((projection - floor) / (1 - floor), 0, 1);
      const residual = Math.hypot(...direction.map((z, c) => data[p + c] - bg[c] - projection * z));
      if (residual > 30) a *= clamp2(1 - (residual - 30) / 45, 0, 1);
    } else {
      a = clamp2((dist - low) / (high - low), 0, 1);
      a = a * a * (3 - 2 * a);
    }
    a *= data[p + 3] / 255;
    if (a > 0.08) {
      count++;
      minX = Math.min(x, minX);
      maxX = Math.max(x, maxX);
      minY = Math.min(y, minY);
      maxY = Math.max(y, maxY);
    }
    for (let c = 0; c < 3; c++) output[q + c] = a > 0 ? light ? ink[c] : clamp2(Math.round(bg[c] + (data[p + c] - bg[c]) / Math.max(0.2, a)), 0, 255) : 0;
    output[q + 3] = Math.round(a * 255);
  }
  if (light) {
    const distance = new Uint8Array(cw * ch).fill(255), queue = new Int32Array(cw * ch);
    let head = 0, tail = 0, peak = 0;
    for (let k = 0; k < cw * ch; k++) peak = Math.max(peak, output[k * 4 + 3]);
    const seed = Math.min(76, peak * 0.6);
    for (let k = 0; k < cw * ch; k++) if (output[k * 4 + 3] >= seed) {
      distance[k] = 0;
      queue[tail++] = k;
    }
    while (head < tail) {
      const k = queue[head++], x = k % cw, y = Math.floor(k / cw);
      if (distance[k] >= 3) continue;
      for (let yy = Math.max(0, y - 1); yy <= Math.min(ch - 1, y + 1); yy++) for (let xx = Math.max(0, x - 1); xx <= Math.min(cw - 1, x + 1); xx++) {
        const q = yy * cw + xx;
        if (distance[q] === 255 && output[q * 4 + 3] > 5) {
          distance[q] = distance[k] + 1;
          queue[tail++] = q;
        }
      }
    }
    for (let k = 0; k < cw * ch; k++) if (distance[k] === 255) output.fill(0, k * 4, k * 4 + 4);
  }
  const cleaned = light ? { data: output, width: cw, height: ch } : cleanMatte({ data: output, width: cw, height: ch }, 1);
  output = (contract ? contractAlpha1px(cleaned) : cleaned).data;
  if (light && contract) {
    const alpha = (x, y) => x < 0 || y < 0 || x >= cw || y >= ch ? 0 : cleaned.data[(y * cw + x) * 4 + 3];
    for (let y = 1; y < ch - 1; y++) for (let x = 1; x < cw - 1; x++) {
      const q = (y * cw + x) * 4, a = cleaned.data[q + 3];
      if (a > 100 && output[q + 3] < a && (alpha(x - 1, y) < a * 0.55 && alpha(x + 1, y) < a * 0.55 || alpha(x, y - 1) < a * 0.55 && alpha(x, y + 1) < a * 0.55)) output.set(cleaned.data.subarray(q, q + 4), q);
    }
  }
  count = 0;
  minX = cw;
  minY = ch;
  maxX = maxY = -1;
  for (let y = 0; y < ch; y++) for (let x = 0; x < cw; x++) if (output[(y * cw + x) * 4 + 3] > 20) {
    count++;
    minX = Math.min(minX, x);
    minY = Math.min(minY, y);
    maxX = Math.max(maxX, x);
    maxY = Math.max(maxY, y);
  }
  if (!count) throw new Error("Tasar\u0131m ayr\u0131lamad\u0131. Alan\u0131 veya zemin temizleme seviyesini de\u011Fi\u015Ftirin.");
  return { data: output, width: cw, height: ch, method: light ? "light-ink" : "colour", bounds: { x: minX, y: minY, width: maxX - minX + 1, height: maxY - minY + 1 }, coverage: count / (cw * ch), source: { x: x0, y: y0, width: cw, height: ch } };
}

// src/detail.mjs
var clamp3 = (v, min = 0, max = 255) => Math.max(min, Math.min(max, v));
function refineDetails(image, { amount = 2.1 } = {}) {
  const { width: w, height: h, data: source } = image, data = new Uint8ClampedArray(source), weights = [1, 8, 28, 56, 70, 56, 28, 8, 1];
  const horizontal = new Float32Array(w * h * 4);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const k = (y * w + x) * 4;
    for (let dx = -4; dx <= 4; dx++) {
      const q = (y * w + clamp3(x + dx, 0, w - 1)) * 4, weight = weights[dx + 4] / 256, a = source[q + 3] / 255;
      horizontal[k + 3] += source[q + 3] * weight;
      for (let c = 0; c < 3; c++) horizontal[k + c] += source[q + c] * a * weight;
    }
  }
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const k = (y * w + x) * 4, a = source[k + 3];
    if (!a) {
      data.fill(0, k, k + 4);
      continue;
    }
    const blur = [0, 0, 0, 0];
    for (let dy = -4; dy <= 4; dy++) {
      const q = (clamp3(y + dy, 0, h - 1) * w + x) * 4, weight = weights[dy + 4] / 256;
      for (let c = 0; c < 4; c++) blur[c] += horizontal[q + c] * weight;
    }
    data[k + 3] = clamp3(Math.round(a + clamp3(amount * (a - blur[3]), -80, 80)), Math.min(a, 4), 255);
    const luma = (r, g, b) => 0.2126 * r + 0.7152 * g + 0.0722 * b;
    const base = luma(source[k], source[k + 1], source[k + 2]), alpha = blur[3] / 255;
    const mean = alpha > 1e-5 ? luma(blur[0] / alpha, blur[1] / alpha, blur[2] / alpha) : base;
    const delta = clamp3((base - mean) * amount * 0.45, -12, 12);
    for (let c = 0; c < 3; c++) data[k + c] = clamp3(Math.round(source[k + c] + delta));
  }
  return { data, width: w, height: h };
}

// <stdin>
var root = "C:\\Users\\USER\\Documents\\Codex\\2026-10-17\\referenced-chatgpt-conversation-this-is-an\\outputs\\dtf-studio";
var dir = "C:\\Users\\USER\\Documents\\Codex\\2026-10-17\\referenced-chatgpt-conversation-this-is-an\\work\\netlik-qa";
var prefix = "/@upscalerjs/esrgan-slim@1.0.0/";
var fetchOriginal = globalThis.fetch;
globalThis.fetch = async (url, options) => {
  const s = String(url), i = s.indexOf(prefix);
  if (i < 0) return fetchOriginal(url, options);
  return new Response(await (0, import_promises.readFile)(import_node_path.default.join(root, "node_modules/@upscalerjs/esrgan-slim", s.slice(i + prefix.length).split("?")[0])), { status: 200 });
};
(async () => {
  const src = await (0, import_sharp.default)("C:/Users/USER/AppData/Local/Temp/codex-clipboard-6c26b5a1-4313-4b82-818b-552d015e147f.png").extract({ left: 65, top: 54, width: 763, height: 564 }).resize(334, 247).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  const isolated = isolatePrint({ data: src.data, width: 334, height: 247 }, { x: 0, y: 0, width: 334, height: 247 }, 8, { contract: false, inkMode: "light" });
  await (0, import_sharp.default)(Buffer.from(isolated.data), { raw: { width: 334, height: 247, channels: 4 } }).png().toFile(import_node_path.default.join(dir, "sat-source.png"));
  wasm.setWasmPaths(root.replaceAll("\\", "/") + "/node_modules/@tensorflow/tfjs-backend-wasm/dist/");
  await tf4.setBackend("wasm");
  await tf4.ready();
  const rgb = new Uint8Array(334 * 247 * 3);
  for (let i = 0; i < 334 * 247; i++) for (let c = 0; c < 3; c++) rgb[i * 3 + c] = isolated.data[i * 4 + c];
  const input = tf4.tensor3d(rgb, [247, 334, 3], "int32"), upscaler = new browser_default({ model: x2_default }), start = Date.now();
  const out = await upscaler.upscale(input, { output: "tensor", patchSize: 64, padding: 8 }), values = await out.data();
  const resized = await (0, import_sharp.default)(Buffer.from(isolated.data), { raw: { width: 334, height: 247, channels: 4 } }).resize(668, 494, { kernel: "cubic" }).raw().toBuffer();
  for (let i = 0; i < 668 * 494; i++) for (let c = 0; c < 3; c++) resized[i * 4 + c] = resized[i * 4 + 3] ? Math.max(0, Math.min(255, Math.round(values[i * 3 + c]))) : 0;
  const refined = refineDetails({ data: resized, width: 668, height: 494 });
  await (0, import_sharp.default)(Buffer.from(refined.data), { raw: { width: 668, height: 494, channels: 4 } }).png().toFile(import_node_path.default.join(root, "../SAT-Ikinci-Kademe-Deneme.png"));
  const before = await (0, import_sharp.default)(Buffer.from(isolated.data), { raw: { width: 334, height: 247, channels: 4 } }).resize(668, 494).flatten({ background: "#10182b" }).png().toBuffer(), after = await (0, import_sharp.default)(Buffer.from(refined.data), { raw: { width: 668, height: 494, channels: 4 } }).flatten({ background: "#10182b" }).png().toBuffer();
  await (0, import_sharp.default)({ create: { width: 1356, height: 544, channels: 3, background: "#f5f6fa" } }).composite([{ input: before, left: 0, top: 50 }, { input: after, left: 688, top: 50 }, { input: Buffer.from('<svg width="1356" height="50"><text x="15" y="32" font-size="22" font-family="Arial">Mevcut sonuc (ekran orneginden)</text><text x="705" y="32" font-size="22" font-family="Arial">AI 2x + ikinci kademe netlik</text></svg>'), left: 0, top: 0 }]).png().toFile(import_node_path.default.join(root, "../SAT-Netlik-Karsilastirma.png"));
  console.log(JSON.stringify({ backend: tf4.getBackend(), milliseconds: Date.now() - start, width: 668, height: 494 }));
  input.dispose();
  out.dispose();
  await upscaler.dispose();
})().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
