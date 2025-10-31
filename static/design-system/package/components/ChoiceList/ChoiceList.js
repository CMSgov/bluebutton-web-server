"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = exports.ChoiceList = void 0;

var _propTypes = _interopRequireDefault(require("prop-types"));

var _Choice = _interopRequireDefault(require("./Choice"));

var _FormLabel = require("../FormLabel");

var _react = _interopRequireDefault(require("react"));

var _classnames = _interopRequireDefault(require("classnames"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

function _extends() { _extends = Object.assign || function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; }; return _extends.apply(this, arguments); }

function ownKeys(object, enumerableOnly) { var keys = Object.keys(object); if (Object.getOwnPropertySymbols) { var symbols = Object.getOwnPropertySymbols(object); if (enumerableOnly) { symbols = symbols.filter(function (sym) { return Object.getOwnPropertyDescriptor(object, sym).enumerable; }); } keys.push.apply(keys, symbols); } return keys; }

function _objectSpread(target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i] != null ? arguments[i] : {}; if (i % 2) { ownKeys(Object(source), true).forEach(function (key) { _defineProperty(target, key, source[key]); }); } else if (Object.getOwnPropertyDescriptors) { Object.defineProperties(target, Object.getOwnPropertyDescriptors(source)); } else { ownKeys(Object(source)).forEach(function (key) { Object.defineProperty(target, key, Object.getOwnPropertyDescriptor(source, key)); }); } } return target; }

function _defineProperty(obj, key, value) { if (key in obj) { Object.defineProperty(obj, key, { value: value, enumerable: true, configurable: true, writable: true }); } else { obj[key] = value; } return obj; }

function _objectWithoutProperties(source, excluded) { if (source == null) return {}; var target = _objectWithoutPropertiesLoose(source, excluded); var key, i; if (Object.getOwnPropertySymbols) { var sourceSymbolKeys = Object.getOwnPropertySymbols(source); for (i = 0; i < sourceSymbolKeys.length; i++) { key = sourceSymbolKeys[i]; if (excluded.indexOf(key) >= 0) continue; if (!Object.prototype.propertyIsEnumerable.call(source, key)) continue; target[key] = source[key]; } } return target; }

function _objectWithoutPropertiesLoose(source, excluded) { if (source == null) return {}; var target = {}; var sourceKeys = Object.keys(source); var key, i; for (i = 0; i < sourceKeys.length; i++) { key = sourceKeys[i]; if (excluded.indexOf(key) >= 0) continue; target[key] = source[key]; } return target; }

var ChoiceList = function ChoiceList(props) {
  var onBlur = props.onBlur,
      onComponentBlur = props.onComponentBlur,
      choices = props.choices,
      listProps = _objectWithoutProperties(props, ["onBlur", "onComponentBlur", "choices"]);

  if (process.env.NODE_ENV !== 'production') {
    if (props.type !== 'checkbox' && props.choices.length === 1) {
      console.warn("[Warning]: Use type=\"checkbox\" for components with only one choice. A single radio button is disallowed because it prevents users from deselecting the field.");
    }
  }

  var choiceRefs = [];

  var handleBlur = function handleBlur(evt) {
    if (onBlur) onBlur(evt);
    if (onComponentBlur) handleComponentBlur(evt);
  };

  var handleComponentBlur = function handleComponentBlur(evt) {
    // The active element is always the document body during a focus
    // transition, so in order to check if the newly focused element
    // is one of our choices, we're going to have to wait a bit.
    setTimeout(function () {
      if (!choiceRefs.includes(document.activeElement)) {
        onComponentBlur(evt);
      }
    }, 20);
  };

  var _useFormLabel = (0, _FormLabel.useFormLabel)(_objectSpread(_objectSpread({}, listProps), {}, {
    labelComponent: 'legend',
    wrapperIsFieldset: true
  })),
      labelProps = _useFormLabel.labelProps,
      fieldProps = _useFormLabel.fieldProps,
      wrapperProps = _useFormLabel.wrapperProps,
      bottomError = _useFormLabel.bottomError;

  var choiceItems = choices.map(function (choiceProps) {
    var completeChoiceProps = _objectSpread(_objectSpread({}, choiceProps), {}, {
      inversed: props.inversed,
      name: props.name,
      // onBlur: (onBlur || onComponentBlur) && handleBlur,
      onBlur: handleBlur,
      onChange: props.onChange,
      size: props.size,
      type: props.type,
      inputClassName: (0, _classnames.default)(choiceProps.inputClassName, {
        'ds-c-choice--error': props.errorMessage
      }),
      disabled: choiceProps.disabled || props.disabled,
      // Individual choices can be disabled as well as the entire field
      inputRef: function inputRef(ref) {
        choiceRefs.push(ref);

        if (choiceProps.inputRef) {
          choiceProps.inputRef(ref);
        }
      }
    });

    return /*#__PURE__*/_react.default.createElement(_Choice.default, _extends({
      key: choiceProps.value
    }, completeChoiceProps));
  });
  return /*#__PURE__*/_react.default.createElement("fieldset", wrapperProps, /*#__PURE__*/_react.default.createElement(_FormLabel.FormLabel, labelProps), choiceItems, bottomError);
};

exports.ChoiceList = ChoiceList;
ChoiceList.propTypes = {
  /**
     * Array of [`Choice`]({{root}}/components/choice/#components.choice.react) data objects to be rendered.
     */
  choices: _propTypes.default.array.isRequired,

  /**
     * Additional classes to be added to the root element.
     */
  className: _propTypes.default.string,

  /**
     * Disables the entire field.
     */
  disabled: _propTypes.default.bool,

  /**
     * Additional hint text to display
     */
  hint: _propTypes.default.node,

  /**
     * Text showing the requirement ("Required", "Optional", etc.). See [Required and Optional Fields]({{root}}/guidelines/forms/#required-and-optional-fields).
     */
  requirementLabel: _propTypes.default.node,

  /**
     * Applies the "inverse" UI theme
     */
  inversed: _propTypes.default.bool,

  /**
     * Label for the field
     */
  label: _propTypes.default.node.isRequired,

  /**
     * Additional classes to be added to the `FormLabel`.
     */
  labelClassName: _propTypes.default.string,

  /**
     * The field's `name` attribute
     */
  name: _propTypes.default.string.isRequired,

  /**
     * Called anytime any choice is blurred
     */
  onBlur: _propTypes.default.func,

  /**
     * Called when any choice is blurred and the focus does not land on one
     * of the other choices inside this component (i.e., when the whole
     * component loses focus)
     */
  onComponentBlur: _propTypes.default.func,
  onChange: _propTypes.default.func,

  /**
     * Sets the size of the checkbox or radio button
     */
  size: _propTypes.default.oneOf(['small']),

  /**
     * Sets the type to render `checkbox` fields or `radio` buttons
     */
  type: _propTypes.default.oneOf(['checkbox', 'radio']).isRequired
};
var _default = ChoiceList;
exports.default = _default;