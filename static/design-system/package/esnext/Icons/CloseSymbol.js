import React from 'react';
import { CloseIconThin } from '@cmsgov/design-system';

var Close = function Close(_ref) {
  var className = _ref.className;
  console.error("[Deprecated]: Please use the <CloseIconThin /> component with 'ds-c-icon-color--error' CSS class instead. This component will be removed in a future release.");
  return /*#__PURE__*/React.createElement(CloseIconThin, {
    className: className
  });
};

export default Close;