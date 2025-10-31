"use strict";

function _typeof(obj) { "@babel/helpers - typeof"; if (typeof Symbol === "function" && typeof Symbol.iterator === "symbol") { _typeof = function _typeof(obj) { return typeof obj; }; } else { _typeof = function _typeof(obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; }; } return _typeof(obj); }

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = exports.Choice = void 0;

var _propTypes = _interopRequireDefault(require("prop-types"));

var _evEmitter = _interopRequireDefault(require("ev-emitter"));

var _FormLabel = _interopRequireDefault(require("../FormLabel/FormLabel"));

var _react = _interopRequireDefault(require("react"));

var _classnames = _interopRequireDefault(require("classnames"));

var _uniqueId = _interopRequireDefault(require("lodash/uniqueId"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

function _extends() { _extends = Object.assign || function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; }; return _extends.apply(this, arguments); }

function _objectWithoutProperties(source, excluded) { if (source == null) return {}; var target = _objectWithoutPropertiesLoose(source, excluded); var key, i; if (Object.getOwnPropertySymbols) { var sourceSymbolKeys = Object.getOwnPropertySymbols(source); for (i = 0; i < sourceSymbolKeys.length; i++) { key = sourceSymbolKeys[i]; if (excluded.indexOf(key) >= 0) continue; if (!Object.prototype.propertyIsEnumerable.call(source, key)) continue; target[key] = source[key]; } } return target; }

function _objectWithoutPropertiesLoose(source, excluded) { if (source == null) return {}; var target = {}; var sourceKeys = Object.keys(source); var key, i; for (i = 0; i < sourceKeys.length; i++) { key = sourceKeys[i]; if (excluded.indexOf(key) >= 0) continue; target[key] = source[key]; } return target; }

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

function _defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } }

function _createClass(Constructor, protoProps, staticProps) { if (protoProps) _defineProperties(Constructor.prototype, protoProps); if (staticProps) _defineProperties(Constructor, staticProps); return Constructor; }

function _inherits(subClass, superClass) { if (typeof superClass !== "function" && superClass !== null) { throw new TypeError("Super expression must either be null or a function"); } subClass.prototype = Object.create(superClass && superClass.prototype, { constructor: { value: subClass, writable: true, configurable: true } }); if (superClass) _setPrototypeOf(subClass, superClass); }

function _setPrototypeOf(o, p) { _setPrototypeOf = Object.setPrototypeOf || function _setPrototypeOf(o, p) { o.__proto__ = p; return o; }; return _setPrototypeOf(o, p); }

function _createSuper(Derived) { var hasNativeReflectConstruct = _isNativeReflectConstruct(); return function _createSuperInternal() { var Super = _getPrototypeOf(Derived), result; if (hasNativeReflectConstruct) { var NewTarget = _getPrototypeOf(this).constructor; result = Reflect.construct(Super, arguments, NewTarget); } else { result = Super.apply(this, arguments); } return _possibleConstructorReturn(this, result); }; }

function _possibleConstructorReturn(self, call) { if (call && (_typeof(call) === "object" || typeof call === "function")) { return call; } else if (call !== void 0) { throw new TypeError("Derived constructors may only return object or undefined"); } return _assertThisInitialized(self); }

function _assertThisInitialized(self) { if (self === void 0) { throw new ReferenceError("this hasn't been initialised - super() hasn't been called"); } return self; }

function _isNativeReflectConstruct() { if (typeof Reflect === "undefined" || !Reflect.construct) return false; if (Reflect.construct.sham) return false; if (typeof Proxy === "function") return true; try { Boolean.prototype.valueOf.call(Reflect.construct(Boolean, [], function () {})); return true; } catch (e) { return false; } }

function _getPrototypeOf(o) { _getPrototypeOf = Object.setPrototypeOf ? Object.getPrototypeOf : function _getPrototypeOf(o) { return o.__proto__ || Object.getPrototypeOf(o); }; return _getPrototypeOf(o); }

function _defineProperty(obj, key, value) { if (key in obj) { Object.defineProperty(obj, key, { value: value, enumerable: true, configurable: true, writable: true }); } else { obj[key] = value; } return obj; }

/** Used to emit events to all Choice components */
var dsChoiceEmitter = new _evEmitter.default();

var Choice = /*#__PURE__*/function (_React$PureComponent) {
  _inherits(Choice, _React$PureComponent);

  var _super = _createSuper(Choice);

  function Choice(props) {
    var _this;

    _classCallCheck(this, Choice);

    _this = _super.call(this, props);

    _defineProperty(_assertThisInitialized(_this), "input", void 0);

    _defineProperty(_assertThisInitialized(_this), "id", void 0);

    _defineProperty(_assertThisInitialized(_this), "isControlled", void 0);

    _defineProperty(_assertThisInitialized(_this), "uncheckEventName", void 0);

    _this.input = null;
    _this.handleChange = _this.handleChange.bind(_assertThisInitialized(_this));
    _this.handleUncheck = _this.handleUncheck.bind(_assertThisInitialized(_this));
    _this.id = _this.props.id || (0, _uniqueId.default)("".concat(_this.props.type, "_").concat(_this.props.name, "_"));

    if (typeof _this.props.checked === 'undefined') {
      _this.isControlled = false; // Since this isn't a controlled component, we need a way
      // to track when the value has changed. This can then be used
      // to identify when to toggle the visibility of (un)checkedChildren

      _this.state = {
        checked: _this.props.defaultChecked
      };
    } else {
      _this.isControlled = true;
    }

    return _this;
  }

  _createClass(Choice, [{
    key: "componentDidMount",
    value: function componentDidMount() {
      // Event emitters are only relevant for uncontrolled radio buttons
      if (!this.isControlled && this.props.type === 'radio') {
        this.uncheckEventName = "".concat(this.props.name, "-uncheck");
        dsChoiceEmitter.on(this.uncheckEventName, this.handleUncheck);
      }
    }
  }, {
    key: "componentWillUnmount",
    value: function componentWillUnmount() {
      // Unbind event emitters are only relevant for uncontrolled radio buttons
      if (!this.isControlled && this.props.type === 'radio') {
        dsChoiceEmitter.off(this.uncheckEventName, this.handleUncheck);
      }
    }
  }, {
    key: "checked",
    value: function checked() {
      if (this.isControlled) {
        return this.props.checked;
      }

      return this.state.checked;
    }
    /**
     * A radio button doesn't receive an onChange event when it is unchecked,
     * so we fire an "uncheck" event when any radio option is selected. This
     * allows us to check each radio options' checked state.
     * @param {String} checkedId - ID of the checked radio option
     */

  }, {
    key: "handleUncheck",
    value: function handleUncheck(checkedId) {
      if (checkedId !== this.id && this.input.checked !== this.state.checked) {
        this.setState({
          checked: this.input.checked
        });
      }
    }
  }, {
    key: "handleChange",
    value: function handleChange(evt) {
      if (this.props.onChange) {
        this.props.onChange(evt);
      }

      if (!this.isControlled) {
        this.setState({
          checked: evt.target.checked
        });

        if (this.props.type === 'radio' && evt.target.checked) {
          // Emit the uncheck event so other radio options update their state
          dsChoiceEmitter.emitEvent(this.uncheckEventName, [this.id]);
        }
      }
    }
  }, {
    key: "render",
    value: function render() {
      var _this2 = this;

      var _this$props = this.props,
          ariaLive = _this$props['aria-live'],
          ariaRelevant = _this$props['aria-relevant'],
          ariaAtomic = _this$props['aria-atomic'],
          checkedChildren = _this$props.checkedChildren,
          className = _this$props.className,
          disabled = _this$props.disabled,
          errorMessage = _this$props.errorMessage,
          errorMessageClassName = _this$props.errorMessageClassName,
          hint = _this$props.hint,
          inversed = _this$props.inversed,
          inputClassName = _this$props.inputClassName,
          label = _this$props.label,
          labelClassName = _this$props.labelClassName,
          requirementLabel = _this$props.requirementLabel,
          size = _this$props.size,
          uncheckedChildren = _this$props.uncheckedChildren,
          inputRef = _this$props.inputRef,
          inputProps = _objectWithoutProperties(_this$props, ["aria-live", "aria-relevant", "aria-atomic", "checkedChildren", "className", "disabled", "errorMessage", "errorMessageClassName", "hint", "inversed", "inputClassName", "label", "labelClassName", "requirementLabel", "size", "uncheckedChildren", "inputRef"]);

      var inputClasses = (0, _classnames.default)(inputClassName, 'ds-c-choice', {
        'ds-c-choice--inverse': inversed,
        'ds-c-choice--small': size === 'small'
      }); // Remove props we have our own implementations for

      if (inputProps.id) delete inputProps.id;
      if (inputProps.onChange) delete inputProps.onChange;
      return /*#__PURE__*/_react.default.createElement("div", {
        className: className,
        "aria-live": ariaLive !== null && ariaLive !== void 0 ? ariaLive : checkedChildren ? 'polite' : null,
        "aria-relevant": ariaRelevant !== null && ariaRelevant !== void 0 ? ariaRelevant : checkedChildren ? 'additions text' : null,
        "aria-atomic": ariaAtomic !== null && ariaAtomic !== void 0 ? ariaAtomic : checkedChildren ? 'false' : null
      }, /*#__PURE__*/_react.default.createElement("div", {
        className: "ds-c-choice-wrapper"
      }, /*#__PURE__*/_react.default.createElement("input", _extends({
        className: inputClasses,
        id: this.id,
        onChange: this.handleChange,
        disabled: disabled,
        ref: function ref(_ref) {
          _this2.input = _ref;

          if (inputRef) {
            inputRef(_ref);
          }
        }
      }, inputProps)), /*#__PURE__*/_react.default.createElement(_FormLabel.default, {
        className: labelClassName,
        fieldId: this.id,
        errorMessage: errorMessage,
        errorMessageClassName: errorMessageClassName,
        hint: hint,
        inversed: inversed,
        requirementLabel: requirementLabel
      }, label)), this.checked() ? checkedChildren : uncheckedChildren);
    }
  }]);

  return Choice;
}(_react.default.PureComponent);

exports.Choice = Choice;

_defineProperty(Choice, "propTypes", {
  /**
     * Sets the input's `checked` state. Use this in combination with `onChange`
     * for a controlled component; otherwise, set `defaultChecked`.
     */
  checked: _propTypes.default.bool,

  /**
     * Content to be shown when the choice is checked. See
     * **Checked children and the expose within pattern** on
     * the Guidance tab for detailed instructions.
     */
  checkedChildren: _propTypes.default.node,

  /**
     * Content to be shown when the choice is not checked
     */
  uncheckedChildren: _propTypes.default.node,

  /**
     * Additional classes to be added to the root `div` element.
     */
  className: _propTypes.default.string,

  /**
     * Additional classes to be added to the `input` element.
     */
  inputClassName: _propTypes.default.string,

  /**
     * Label text or HTML.
     */
  label: _propTypes.default.node,

  /**
     * Additional classes to be added to the `FormLabel`.
     */
  labelClassName: _propTypes.default.string,

  /**
     * Sets the initial `checked` state. Use this for an uncontrolled component;
     * otherwise, use the `checked` property.
     */
  defaultChecked: _propTypes.default.bool,
  disabled: _propTypes.default.bool,
  errorMessage: _propTypes.default.node,

  /**
     * Additional classes to be added to the error message
     */
  errorMessageClassName: _propTypes.default.string,

  /**
     * Access a reference to the `input` element
     */
  inputRef: _propTypes.default.func,

  /**
     * Additional hint text to display below the choice's label
     */
  hint: _propTypes.default.node,

  /**
     * A unique ID to be used for the input field, as well as the label's
     * `for` attribute. A unique ID will be generated if one isn't provided.
     */
  id: _propTypes.default.string,

  /**
     * Text showing the requirement ("Required", "Optional", etc.). See [Required and Optional Fields]({{root}}/guidelines/forms/#required-and-optional-fields).
     */
  requirementLabel: _propTypes.default.node,

  /**
     * Applies the "inverse" UI theme
     */
  inversed: _propTypes.default.bool,
  size: _propTypes.default.oneOf(['small']),

  /**
     * The `input` field's `name` attribute
     */
  name: _propTypes.default.string.isRequired,
  onBlur: _propTypes.default.func,
  onChange: _propTypes.default.func,

  /**
     * Sets the type to render `checkbox` fields or `radio` buttons
     */
  type: _propTypes.default.oneOf(['checkbox', 'radio']).isRequired,

  /**
     * The `input` `value` attribute
     */
  value: _propTypes.default.oneOfType([_propTypes.default.number, _propTypes.default.string]).isRequired
});

var _default = Choice;
exports.default = _default;