import React from 'react';
import { CloseIcon } from '@cmsgov/design-system';

var No = function No(_ref) {
  var _ref$className = _ref.className,
      className = _ref$className === void 0 ? '' : _ref$className;
  console.error("[Deprecated]: Please use the <CloseIcon /> component with 'ds-c-icon-color--error' CSS class instead. This component will be removed in a future release.");
  return /*#__PURE__*/React.createElement(CloseIcon, {
    title: "Caret",
    className: "ds-c-icon-color--error ".concat(className)
  });
};

export default No;