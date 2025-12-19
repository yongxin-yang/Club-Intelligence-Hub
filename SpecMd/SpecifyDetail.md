## 2025/12/16
我希望你先做一个前端页面负责用户通过前端向后端"mcp client"发送请求,然后mcp client给大模型发消息，大模型调用mcp server的api,mcp server则负责调用后端的api实现后端数据库读取和写入任务，
为了完成这个任务，你需要将现在的代码分成两层：app,backend1，app中包括前端页面和mcp client还有mcp server(其下有一个文件夹backend1专门负责backend1),backend1就是一个假象的简单项目后端（和这个ClubAIGateway项目无关，主要为了模拟对各个后端接口的接入）
你可以先制定计划，注意要遵循spec-force的原则。