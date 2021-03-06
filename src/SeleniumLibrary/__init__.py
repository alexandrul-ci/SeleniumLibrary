# Copyright 2008-2011 Nokia Networks
# Copyright 2011-2016 Ryan Tomac, Ed Manlove and contributors
# Copyright 2016-     Robot Framework Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import warnings

from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn

from SeleniumLibrary.base import DynamicCore
from SeleniumLibrary.keywords import (AlertKeywords,
                                      BrowserManagementKeywords,
                                      CookieKeywords,
                                      ElementKeywords,
                                      FormElementKeywords,
                                      JavaScriptKeywords,
                                      RunOnFailureKeywords,
                                      ScreenshotKeywords,
                                      SelectElementKeywords,
                                      TableElementKeywords,
                                      WaitingKeywords)
from SeleniumLibrary.locators import ElementFinder
from SeleniumLibrary.utils import (BrowserCache, Deprecated, LibraryListener,
                                   timestr_to_secs)


__version__ = '3.0.0b1'


class SeleniumLibrary(DynamicCore):
    """SeleniumLibrary is a web testing library for Robot Framework.

    This document is about using SeleniumLibrary. For information about
    installation, support, and more please visit the
    [https://github.com/robotframework/SeleniumLibrary|project page].

    SeleniumLibrary uses the Selenium 2 (WebDriver) libraries internally to control a web browser.
    See http://seleniumhq.org/docs/03_webdriver.html for more information on Selenium 2
    and WebDriver.

    SeleniumLibrary runs tests in a real browser instance. It should work in
    most modern browsers and can be used with both Python and Jython interpreters.

    = Before running tests =

    Prior to running test cases using SeleniumLibrary, SeleniumLibrary must be
    imported into your Robot test suite (see `importing` section), and the
    `Open Browser` keyword must be used to open a browser to the desired location.


    *--- Note important change starting with Version 1.7.0 release ---*
    = Locating or specifying elements =

    All keywords in SeleniumLibrary that need to find an element on the page
    take an argument, either a `locator` or now a `webelement`. `locator`
    is a string that describes how to locate an element using a syntax
    specifying different location strategies. `webelement` is a variable that
    holds a WebElement instance, which is a representation of the element.

    *Using locators*
    ---------------
    The locator can be used in two ways. In explicit way, where the strategy
    of the locator is defined as prefix in the locator or in implicit way,
    where there strategy is determined from the locator.

    The implicit way supports two strategies: `xpath` and matching against
    `id` and `name` attributes. If locator starts with `//` or `(//` then
    `xpath` strategy will be used. Determining `(//`  as xpath is supported
    from release 3.0.0 onwards. If locator does not start with `//` or `(//`,
    then it is matched against the `id` and `name` key attributes of
    elements. Example

    | Click Element    my_element    # id and name attribute matching
    | Click Element    //div         # xpath
    | Click Element    (//div)[2]    # xpath

    In the explicit way, it is possible to specify the approach
    SeleniumLibrary should take to find an element by specifying a lookup
    strategy with a locator prefix. Supported strategies are:

    | *Strategy* | *Example*                               | *Description*                                   |
    | identifier | Click Element `|` identifier=my_element | Matches by @id or @name attribute               |
    | id         | Click Element `|` id=my_element         | Matches by @id attribute                        |
    | name       | Click Element `|` name=my_element       | Matches by @name attribute                      |
    | xpath      | Click Element `|` xpath=//div[@id='my_element'] | Matches with arbitrary XPath expression |
    | dom        | Click Element `|` dom=document.images[56] | Matches with arbitrary DOM express            |
    | link       | Click Element `|` link=My Link          | Matches anchor elements by their link text      |
    | partial link | Click Element `|` partial link=y Lin  | Matches anchor elements by their partial link text |
    | css        | Click Element `|` css=div.my_class      | Matches by CSS selector                         |
    | class      | Click Element `|` class=my_class       | Matches by class name selector                  |
    | jquery     | Click Element `|` jquery=div.my_class   | Matches by jQuery/sizzle selector                         |
    | sizzle     | Click Element `|` sizzle=div.my_class   | Matches by jQuery/sizzle selector                         |
    | tag        | Click Element `|` tag=div               | Matches by HTML tag name                        |
    | default*   | Click Link    `|` default=page?a=b      | Matches key attributes with value after first '=' |
    * Explicitly specifying the default strategy is only necessary if locating
    elements by matching key attributes is desired and an attribute value
    contains a '='. The following would fail because it appears as if _page?a_
    is the specified lookup strategy:
    | Click Link    page?a=b
    This can be fixed by changing the locator to:
    | Click Link    default=page?a=b

    Please note that jQuery is not provided by SeleniumLibrary
    and if there is need to use jQuery locators, the system
    under test must provide the jQuery library.

    *Using webelements*
    ------------------
    Starting with version 1.7 of the SeleniumLibrary, one can pass an argument
    that contains a WebElement instead of a string locator. To get a WebElement,
    use the new `Get WebElements` keyword.  For example:

    | ${elem} =      | Get WebElement | id=my_element |
    | Click Element  | ${elem} |                      |

    Locating Tables, Table Rows, Columns, etc.
    ------------------------------------------
    Table related keywords, such as `Table Should Contain`, work differently.
    By default, when a table locator value is provided, it will search for
    a table with the specified `id` attribute. For example:

    | Table Should Contain    my_table    text

    More complex table lookup strategies are also supported:

    | *Strategy* | *Example*                                                          | *Description*                     |
    | css        | Table Should Contain `|` css=table.my_class `|` text               | Matches by @id or @name attribute |
    | xpath      | Table Should Contain `|` xpath=//table/[@name="my_table"] `|` text | Matches by @id or @name attribute |

    = Custom Locators =

    If more complex lookups are required than what is provided through the default locators, custom lookup strategies can
    be created. Using custom locators is a two part process. First, create a keyword that returns the WebElement
    that should be acted on.

    | Custom Locator Strategy | [Arguments] | ${browser} | ${criteria} | ${tag} | ${constraints} |
    |   | ${retVal}= | Execute Javascript | return window.document.getElementById('${criteria}'); |
    |   | [Return] | ${retVal} |

    This keyword is a reimplementation of the basic functionality of the `id` locator where `${browser}` is a reference
    to the WebDriver instance and `${criteria}` is the text of the locator (i.e. everything that comes after the = sign).
    To use this locator it must first be registered with `Add Location Strategy`.

    | Add Location Strategy    custom    Custom Locator Strategy

    The first argument of `Add Location Strategy` specifies the name of the lookup strategy (which must be unique). After
    registration of the lookup strategy, the usage is the same as other locators. See `Add Location Strategy` for more details.

    = Timeouts =

    There are several `Wait ...` keywords that take timeout as an
    argument. All of these timeout arguments are optional. The timeout
    used by all of them can be set globally using the
    `Set Selenium Timeout` keyword. The same timeout also applies to
    `Execute Async Javascript`.

    All timeouts can be given as numbers considered seconds (e.g. 0.5 or 42)
    or in Robot Framework's time syntax (e.g. '1.5 seconds' or '1 min 30 s').
    For more information about the time syntax see the
    [http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#time-format|Robot Framework User Guide].

    = Boolean arguments =

    Some keywords accept arguments that are handled as Boolean values true or
    false. If such an argument is given as a string, it is considered false if
    it is either empty or case-insensitively equal to ``false``, ``no`` or
    ``none``. Other strings are considered true regardless their value, and
    other argument types are tested using same
    [https://docs.python.org/2/library/stdtypes.html#truth-value-testing|rules as in Python].

    True examples:
    | Set Screenshot Directory | ${OUTPUT_DIR}/screenshots | persist=True    | # Strings are generally true.    |
    | Set Screenshot Directory | ${OUTPUT_DIR}/screenshots | persist=yes     | # Same as the above.             |
    | Set Screenshot Directory | ${OUTPUT_DIR}/screenshots | persist=${TRUE} | # Python True is true.           |
    | Set Screenshot Directory | ${OUTPUT_DIR}/screenshots | persist=${42}   | # Numbers other than 0 are true. |

    False examples:
    | Set Screenshot Directory | ${OUTPUT_DIR}/screenshots | persist=False    | # String false is false.        |
    | Set Screenshot Directory | ${OUTPUT_DIR}/screenshots | persist=no       | # Also string no is false.      |
    | Set Screenshot Directory | ${OUTPUT_DIR}/screenshots | persist=NONE     | # String NONE is false.         |
    | Set Screenshot Directory | ${OUTPUT_DIR}/screenshots | persist=${EMPTY} | # Empty string is false.        |
    | Set Screenshot Directory | ${OUTPUT_DIR}/screenshots | persist=${FALSE} | # Python False is false.        |
    | Set Screenshot Directory | ${OUTPUT_DIR}/screenshots | persist=${NONE}  | # Python None is false.         |

    Note that prior to SeleniumLibrary 3.0, all non-empty strings, including
    ``false``, ``no`` and ``none``, were considered true.
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LIBRARY_VERSION = __version__

    def __init__(self,
                 timeout=5.0,
                 implicit_wait=0.0,
                 run_on_failure='Capture Page Screenshot',
                 screenshot_root_directory=None):

        """SeleniumLibrary can be imported with optional arguments.

        `timeout` is the default timeout used to wait for all waiting actions.
        It can be later set with `Set Selenium Timeout`.

        'implicit_wait' is the implicit timeout that Selenium waits when
        looking for elements.
        It can be later set with `Set Selenium Implicit Wait`.
        See `WebDriver: Advanced Usage`__ section of the SeleniumHQ documentation
        for more information about WebDriver's implicit wait functionality.

        __ http://seleniumhq.org/docs/04_webdriver_advanced.html#explicit-and-implicit-waits

        `run_on_failure` specifies the name of a keyword (from any available
        libraries) to execute when a SeleniumLibrary keyword fails. By default
        `Capture Page Screenshot` will be used to take a screenshot of the current page.
        Using the value "Nothing" will disable this feature altogether. See
        `Register Keyword To Run On Failure` keyword for more information about this
        functionality.

        `screenshot_root_directory` specifies the default root directory that screenshots should be
        stored in. If not provided the default directory will be where robotframework places its logfile.

        Examples:
        | Library `|` SeleniumLibrary `|` 15                                            | # Sets default timeout to 15 seconds                                       |
        | Library `|` SeleniumLibrary `|` 0 `|` 5                                       | # Sets default timeout to 0 seconds and default implicit_wait to 5 seconds |
        | Library `|` SeleniumLibrary `|` 5 `|` run_on_failure=Log Source               | # Sets default timeout to 5 seconds and runs `Log Source` on failure       |
        | Library `|` SeleniumLibrary `|` implicit_wait=5 `|` run_on_failure=Log Source | # Sets default implicit_wait to 5 seconds and runs `Log Source` on failure |
        | Library `|` SeleniumLibrary `|` timeout=10      `|` run_on_failure=Nothing    | # Sets default timeout to 10 seconds and does nothing on failure           |
        """
        self.timeout = timestr_to_secs(timeout)
        self.implicit_wait = timestr_to_secs(implicit_wait)
        self.speed = 0.0
        self.run_on_failure_keyword \
            = RunOnFailureKeywords.resolve_keyword(run_on_failure)
        self._running_on_failure_keyword = False
        self.screenshot_root_directory = screenshot_root_directory
        libraries = [
            AlertKeywords(self),
            BrowserManagementKeywords(self),
            RunOnFailureKeywords(self),
            ElementKeywords(self),
            TableElementKeywords(self),
            FormElementKeywords(self),
            SelectElementKeywords(self),
            JavaScriptKeywords(self),
            CookieKeywords(self),
            ScreenshotKeywords(self),
            WaitingKeywords(self)
        ]
        self._browsers = BrowserCache()
        DynamicCore.__init__(self, libraries)
        self.ROBOT_LIBRARY_LISTENER = LibraryListener()
        self.element_finder = ElementFinder(self)

    _speed_in_secs = Deprecated('_speed_in_secs', 'speed')
    _timeout_in_secs = Deprecated('_timeout_in_secs', 'timeout')
    _implicit_wait_in_secs = Deprecated('_implicit_wait_in_secs',
                                        'implicit_wait')
    _run_on_failure_keyword = Deprecated('_run_on_failure_keyword',
                                         'run_on_failure_keyword')

    def run_keyword(self, name, args, kwargs):
        try:
            return DynamicCore.run_keyword(self, name, args, kwargs)
        except Exception:
            self.failure_occurred()
            raise

    def register_browser(self, browser, alias):
        return self._browsers.register(browser, alias)

    def failure_occurred(self):
        """Method that is executed when a SeleniumLibrary keyword fails.

        By default executes the registered run-on-failure keyword.
        Libraries extending SeleniumLibrary can overwrite this hook
        method if they want to provide custom functionality instead.
        """
        if self._running_on_failure_keyword or not self.run_on_failure_keyword:
            return
        try:
            self._running_on_failure_keyword = True
            BuiltIn().run_keyword(self.run_on_failure_keyword)
        except Exception as err:
            logger.warn("Keyword '%s' could not be run on failure: %s"
                        % (self.run_on_failure_keyword, err))
        finally:
            self._running_on_failure_keyword = False

    @property
    def browser(self):
        """Current active browser"""
        if not self._browsers.current:
            raise RuntimeError('No browser is open')
        return self._browsers.current

    @property
    def _cache(self):
        warnings.warn('"SeleniumLibrary._cache" is deprecated, '
                      'use public API instead.', DeprecationWarning)
        return self._browsers

    def _current_browser(self):
        warnings.warn('"SeleniumLibrary._current_browser" is deprecated, '
                      'use "SeleniumLibrary.browser" instead.',
                      DeprecationWarning)
        return self.browser

    def _run_on_failure(self):
        warnings.warn('"SeleniumLibrary._run_on_failure" is deprecated, '
                      'use "SeleniumLibrary.failure_occurred" instead.',
                      DeprecationWarning)
        self.failure_occurred()
