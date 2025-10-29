"use strict";

function _typeof(obj) { "@babel/helpers - typeof"; if (typeof Symbol === "function" && typeof Symbol.iterator === "symbol") { _typeof = function _typeof(obj) { return typeof obj; }; } else { _typeof = function _typeof(obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; }; } return _typeof(obj); }

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _react = _interopRequireWildcard(require("react"));

var _designSystem = require("@cmsgov/design-system");

var _MedicaregovLogo = _interopRequireDefault(require("../MedicaregovLogo/MedicaregovLogo"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

function _getRequireWildcardCache(nodeInterop) { if (typeof WeakMap !== "function") return null; var cacheBabelInterop = new WeakMap(); var cacheNodeInterop = new WeakMap(); return (_getRequireWildcardCache = function _getRequireWildcardCache(nodeInterop) { return nodeInterop ? cacheNodeInterop : cacheBabelInterop; })(nodeInterop); }

function _interopRequireWildcard(obj, nodeInterop) { if (!nodeInterop && obj && obj.__esModule) { return obj; } if (obj === null || _typeof(obj) !== "object" && typeof obj !== "function") { return { default: obj }; } var cache = _getRequireWildcardCache(nodeInterop); if (cache && cache.has(obj)) { return cache.get(obj); } var newObj = {}; var hasPropertyDescriptor = Object.defineProperty && Object.getOwnPropertyDescriptor; for (var key in obj) { if (key !== "default" && Object.prototype.hasOwnProperty.call(obj, key)) { var desc = hasPropertyDescriptor ? Object.getOwnPropertyDescriptor(obj, key) : null; if (desc && (desc.get || desc.set)) { Object.defineProperty(newObj, key, desc); } else { newObj[key] = obj[key]; } } } newObj.default = obj; if (cache) { cache.set(obj, newObj); } return newObj; }

var SimpleFooter = function SimpleFooter(_ref) {
  var _ref$aboutMedicareLab = _ref.aboutMedicareLabel,
      aboutMedicareLabel = _ref$aboutMedicareLab === void 0 ? 'About Medicare' : _ref$aboutMedicareLab,
      _ref$medicareGlossary = _ref.medicareGlossaryLabel,
      medicareGlossaryLabel = _ref$medicareGlossary === void 0 ? 'Medicare Glossary' : _ref$medicareGlossary,
      _ref$nondiscriminatio = _ref.nondiscriminationLabel,
      nondiscriminationLabel = _ref$nondiscriminatio === void 0 ? 'Nondiscrimination / Accessibility' : _ref$nondiscriminatio,
      _ref$privacyPolicyLab = _ref.privacyPolicyLabel,
      privacyPolicyLabel = _ref$privacyPolicyLab === void 0 ? 'Privacy Policy' : _ref$privacyPolicyLab,
      _ref$privacySettingLa = _ref.privacySettingLabel,
      privacySettingLabel = _ref$privacySettingLa === void 0 ? 'Privacy Setting' : _ref$privacySettingLa,
      _ref$linkingPolicyLab = _ref.linkingPolicyLabel,
      linkingPolicyLabel = _ref$linkingPolicyLab === void 0 ? 'Linking Policy' : _ref$linkingPolicyLab,
      _ref$usingThisSiteLab = _ref.usingThisSiteLabel,
      usingThisSiteLabel = _ref$usingThisSiteLab === void 0 ? 'Using this site' : _ref$usingThisSiteLab,
      _ref$plainWritingLabe = _ref.plainWritingLabel,
      plainWritingLabel = _ref$plainWritingLabe === void 0 ? 'Plain Writing' : _ref$plainWritingLabe,
      _ref$language = _ref.language,
      language = _ref$language === void 0 ? 'en' : _ref$language,
      _ref$websiteInfo = _ref.websiteInfo,
      websiteInfo = _ref$websiteInfo === void 0 ? 'A federal government website managed and paid for by the U.S. Centers for Medicare and Medicaid Services.' : _ref$websiteInfo,
      onClickLinkAnalytics = _ref.onClickLinkAnalytics;
  var footerRef = (0, _react.useRef)();
  (0, _react.useEffect)(function () {
    if (onClickLinkAnalytics) {
      var _footerRef$current;

      (_footerRef$current = footerRef.current) === null || _footerRef$current === void 0 ? void 0 : _footerRef$current.querySelectorAll('a').forEach(function (anchor) {
        anchor.onclick = function () {
          return onClickLinkAnalytics(anchor.href);
        };
      });
    }
  }, [onClickLinkAnalytics]);
  return /*#__PURE__*/_react.default.createElement("footer", {
    className: "m-c-footer",
    ref: footerRef
  }, /*#__PURE__*/_react.default.createElement("div", {
    className: "m-c-footer__linkRow"
  }, /*#__PURE__*/_react.default.createElement("div", {
    className: "m-c-footer__links"
  }, /*#__PURE__*/_react.default.createElement("a", {
    href: "https://www.medicare.gov/about-us"
  }, aboutMedicareLabel), /*#__PURE__*/_react.default.createElement("span", {
    "aria-hidden": "true",
    className: "m-c-footer__delimiter"
  }), /*#__PURE__*/_react.default.createElement("a", {
    href: "https://www.medicare.gov/glossary/a"
  }, medicareGlossaryLabel)), /*#__PURE__*/_react.default.createElement("div", null, /*#__PURE__*/_react.default.createElement("a", {
    href: "https://www.medicare.gov/about-us/accessibility-nondiscrimination-notice"
  }, nondiscriminationLabel), /*#__PURE__*/_react.default.createElement("span", {
    "aria-hidden": "true",
    className: "m-c-footer__delimiter"
  }), /*#__PURE__*/_react.default.createElement("a", {
    href: "https://www.medicare.gov/privacy-policy"
  }, privacyPolicyLabel), /*#__PURE__*/_react.default.createElement("span", {
    "aria-hidden": "true",
    className: "m-c-footer__delimiter"
  }), /*#__PURE__*/_react.default.createElement(_designSystem.Button, {
    className: "SimpleFooter__linkButton",
    variation: "ghost",
    onClick: function onClick() {
      var utag = window.utag;

      if (utag && utag.gdpr && utag.gdpr.showConsentPreferences(language) && typeof window.utag.gdpr.showConsentPreferences === 'function') {
        utag.gdpr.showConsentPreferences();
      }

      if (onClickLinkAnalytics) {
        onClickLinkAnalytics(privacySettingLabel);
      }
    }
  }, privacySettingLabel), /*#__PURE__*/_react.default.createElement("span", {
    "aria-hidden": "true",
    className: "m-c-footer__delimiter"
  }), /*#__PURE__*/_react.default.createElement("a", {
    href: "https://www.cms.gov/About-CMS/Agency-Information/Aboutwebsite/index.html"
  }, linkingPolicyLabel), /*#__PURE__*/_react.default.createElement("span", {
    "aria-hidden": "true",
    className: "m-c-footer__delimiter"
  }), /*#__PURE__*/_react.default.createElement("a", {
    href: "https://www.medicare.gov/about-us/using-this-site"
  }, usingThisSiteLabel), /*#__PURE__*/_react.default.createElement("span", {
    "aria-hidden": "true",
    className: "m-c-footer__delimiter"
  }), /*#__PURE__*/_react.default.createElement("a", {
    href: "https://www.medicare.gov/about-us/plain-writing"
  }, plainWritingLabel))), /*#__PURE__*/_react.default.createElement("div", {
    className: "m-c-footer__identityRow"
  }, /*#__PURE__*/_react.default.createElement(_MedicaregovLogo.default, null), /*#__PURE__*/_react.default.createElement("div", {
    className: "m-c-footer__identityContent"
  }, /*#__PURE__*/_react.default.createElement(_designSystem.HHSLogo, null), /*#__PURE__*/_react.default.createElement("span", {
    className: "m-c-footer__contactAddress"
  }, websiteInfo, /*#__PURE__*/_react.default.createElement("br", null), "7500 Security Boulevard, Baltimore, MD 21244"))));
};

var _default = SimpleFooter;
exports.default = _default;