"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _react = _interopRequireDefault(require("react"));

var _designSystem = require("@cmsgov/design-system");

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

function _extends() { _extends = Object.assign || function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; }; return _extends.apply(this, arguments); }

var defaultProps = {
  className: '',
  title: 'Check with shield',
  viewBox: '0 0 27 32'
};

function CheckShieldIcon(props) {
  var iconCssClasses = "ds-c-icon--check-with-shield ".concat(props.className || '');
  return /*#__PURE__*/_react.default.createElement(_designSystem.SvgIcon, _extends({}, defaultProps, props, {
    className: iconCssClasses
  }), /*#__PURE__*/_react.default.createElement("path", {
    d: "M13.5,0 C17.2900201,1.96825397 21.7900201,2.95238095 27,2.95238095 L27,20.6666667 C23,25.5873016 18.5,29.031746 13.5,31 L12.9845422,30.7911217 C8.36147444,28.8638242 4.17181926,25.6569277 0.415576694,21.170432 L0,20.6666667 L0,2.95238095 C5.0095961,2.95238095 9.36277583,2.04250023 13.0595392,0.2227388 L13.5,0 Z M20.963644,9.11804339 C20.6121866,8.77017601 20.0423033,8.77017601 19.6908459,9.11804339 L19.6908459,9.11804339 L11.2499978,17.4726367 L7.30915411,13.572082 C6.95769674,13.2241798 6.38781337,13.2241798 6.03635599,13.572082 L6.03635599,13.572082 L4.76359303,14.831879 C4.41213566,15.1797812 4.41213566,15.7438086 4.76359303,16.091676 L4.76359303,16.091676 L10.6135987,21.8819262 C10.9650561,22.2298283 11.5349043,22.2298283 11.8863969,21.881961 L11.8863969,21.881961 L22.236407,11.6376374 C22.5878643,11.2897352 22.5878643,10.7257077 22.236407,10.3778404 L22.236407,10.3778404 Z"
  }));
}

var _default = CheckShieldIcon;
exports.default = _default;