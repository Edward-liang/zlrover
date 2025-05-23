// Copyright 2024 The DLRover Authors. All rights reserved.
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#pragma once
#include <butil/logging.h>

#include "xpu_timer/common/util.h"

#define XLOG(level) \
  LOG(level) << ::xpu_timer::util::config::GlobalConfig::rank_str

namespace xpu_timer {
void setLoggingPath(bool is_brpc_server);
}
