function _extends() { _extends = Object.assign || function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; }; return _extends.apply(this, arguments); }

import React from 'react';
import classNames from 'classnames';
import uniqueId from 'lodash/uniqueId';
import { SvgIcon } from '@cmsgov/design-system';
var defaultProps = {
  className: '',
  title: 'Empty Star'
};

var RoundedStarEmptyIcon = function RoundedStarEmptyIcon(props) {
  var clipPath1 = uniqueId('empty_clip_path_');
  var clipPath2 = uniqueId('empty_clip_path_');
  var clipPath3 = uniqueId('empty_clip_path_');
  var iconCssClasses = classNames('ds-c-icon--rounded-star', 'ds-c-icon--rounded-star-empty', props.className);
  return /*#__PURE__*/React.createElement(SvgIcon, _extends({}, defaultProps, props, {
    className: iconCssClasses
  }), /*#__PURE__*/React.createElement("clipPath", {
    id: clipPath1
  }, /*#__PURE__*/React.createElement("path", {
    d: "M11,3.6L8.8,8.3L3.9,9C3,9.2,2.7,10.3,3.3,10.9l3.6,3.6L6,19.7c-0.2,0.9,0.8,1.6,1.6,1.2l4.4-2.4l4.4,2.4 c0.8,0.4,1.7-0.3,1.6-1.2l-0.8-5.1l3.6-3.6c0.6-0.7,0.3-1.8-0.6-1.9l-4.9-0.7L13,3.6C12.6,2.8,11.4,2.8,11,3.6z"
  })), /*#__PURE__*/React.createElement("clipPath", {
    id: clipPath2
  }, /*#__PURE__*/React.createElement("rect", {
    x: "-8",
    y: "-8",
    width: "40",
    height: "40"
  })), /*#__PURE__*/React.createElement("clipPath", {
    id: clipPath3
  }, /*#__PURE__*/React.createElement("rect", {
    x: "3",
    y: "3",
    width: "18",
    height: "18"
  })), /*#__PURE__*/React.createElement("g", {
    clipPath: "url(#".concat(clipPath1, ")")
  }, /*#__PURE__*/React.createElement("g", {
    clipPath: "url(#".concat(clipPath2, ")"),
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2,
    strokeMiterlimit: 10
  }, /*#__PURE__*/React.createElement("path", {
    className: "EmptyStarPath",
    clipPath: "url(#".concat(clipPath3, ")"),
    d: "M11,3.6L8.8,8.3L3.9,9C3,9.2,2.7,10.3,3.3,10.9l3.6,3.6L6,19.7c-0.2,0.9,0.8,1.6,1.6,1.2l4.4-2.4l4.4,2.4 c0.8,0.4,1.7-0.3,1.6-1.2l-0.8-5.1l3.6-3.6c0.6-0.7,0.3-1.8-0.6-1.9l-4.9-0.7L13,3.6C12.6,2.8,11.4,2.8,11,3.6z"
  }))));
};

export default RoundedStarEmptyIcon;